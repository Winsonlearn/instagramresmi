from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
import os
import time
import json
from datetime import datetime

from app.extension import db
from sqlalchemy.orm import joinedload
from app.models.stories import Story
from app.models.story_views import StoryView
from app.models.users import User
from app.models.follows import Follow
from app.utils import save_story_media

stories_bp = Blueprint("stories", __name__, url_prefix="/stories")

@stories_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new story"""
    if request.method == "POST":
        # Check if file is present
        if 'media' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['media']
        if not file or not file.filename:
            return jsonify({'error': 'Please select an image or video'}), 400
        
        try:
            timestamp = int(time.time() * 1000)
            filename, media_type, error = save_story_media(file, current_user.id, timestamp)
            
            if not filename:
                return jsonify({'error': error or 'Error uploading media'}), 400
            
            # Get text overlay if provided (JSON string)
            text_overlay = request.form.get('text_overlay', None)
            
            # Create story with 24-hour expiration
            story = Story(
                user_id=current_user.id,
                media_url=filename,
                media_type=media_type,
                text_overlay=text_overlay,
                expires_at=Story.create_expires_at()
            )
            db.session.add(story)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'story_id': story.id,
                'message': 'Story created successfully!'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Error creating story. Please try again.'}), 500
    
    return render_template("stories/create.html")

@stories_bp.route("/")
@login_required
def view_all():
    """View all stories from users you follow"""
    # Get users you follow
    following_ids = [f.followed_id for f in current_user.following.all()]
    following_ids.append(current_user.id)  # Include your own stories
    
    # Get active stories (not expired) from following users
    stories_query = Story.query.filter(
        Story.user_id.in_(following_ids),
        Story.expires_at > datetime.utcnow()
    ).options(
        joinedload(Story.user)
    ).order_by(Story.created_at.desc())
    
    # Group stories by user
    stories_by_user = {}
    for story in stories_query.all():
        if story.user_id not in stories_by_user:
            stories_by_user[story.user_id] = []
        stories_by_user[story.user_id].append(story)
    
    return render_template("stories/view_all.html", stories_by_user=stories_by_user)

@stories_bp.route("/<int:story_id>")
@login_required
def view(story_id):
    """View a specific story"""
    story = Story.query.options(joinedload(Story.user)).get_or_404(story_id)
    
    # Check if expired
    if story.is_expired():
        flash('This story has expired.', 'info')
        return redirect(url_for('stories.view_all'))
    
    # Check if user can view (following or own story)
    if story.user_id != current_user.id:
        is_following = current_user.is_following(story.user)
        if not is_following:
            flash('You must follow this user to view their story.', 'error')
            return redirect(url_for('stories.view_all'))
    
    # Mark as viewed if not already viewed
    if not story.is_viewed_by(current_user):
        view = StoryView(story_id=story.id, viewer_id=current_user.id)
        db.session.add(view)
        db.session.commit()
    
    return render_template("stories/view.html", story=story)

@stories_bp.route("/<int:story_id>/view", methods=["POST"])
@login_required
def mark_viewed(story_id):
    """Mark a story as viewed"""
    story = Story.query.get_or_404(story_id)
    
    if story.is_expired():
        return jsonify({'error': 'Story has expired'}), 400
    
    # Check if already viewed
    if not story.is_viewed_by(current_user):
        view = StoryView(story_id=story.id, viewer_id=current_user.id)
        db.session.add(view)
        db.session.commit()
    
    return jsonify({'success': True, 'view_count': story.view_count()})

@stories_bp.route("/<int:story_id>/react", methods=["POST"])
@login_required
def react(story_id):
    """Add a reaction to a story (quick emoji)"""
    story = Story.query.get_or_404(story_id)
    
    if story.is_expired():
        return jsonify({'error': 'Story has expired'}), 400
    
    reaction = request.json.get('reaction', '❤️')
    # For now, we'll just store it in text_overlay JSON
    # In a full implementation, you might want a separate StoryReaction model
    
    return jsonify({'success': True, 'reaction': reaction})

@stories_bp.route("/<int:story_id>/highlight", methods=["POST"])
@login_required
def add_to_highlight(story_id):
    """Add story to highlights"""
    story = Story.query.get_or_404(story_id)
    
    if story.user_id != current_user.id:
        return jsonify({'error': 'You can only highlight your own stories'}), 403
    
    highlight_title = request.json.get('title', 'Highlights')
    
    try:
        story.is_highlight = True
        story.highlight_title = highlight_title
        db.session.commit()
        return jsonify({'success': True, 'message': 'Story added to highlights'})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Error adding to highlights'}), 500

@stories_bp.route("/<int:story_id>/delete", methods=["POST"])
@login_required
def delete(story_id):
    """Delete a story"""
    story = Story.query.get_or_404(story_id)
    
    if story.user_id != current_user.id:
        flash('You can only delete your own stories.', 'error')
        return redirect(url_for('stories.view_all'))
    
    try:
        # Delete media file
        if story.media_url:
            media_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                'stories',
                story.media_url
            )
            if os.path.exists(media_path) and os.path.isfile(media_path):
                try:
                    os.remove(media_path)
                except OSError:
                    pass
        
        db.session.delete(story)
        db.session.commit()
        flash('Story deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error deleting story. Please try again.', 'error')
    
    return redirect(url_for('stories.view_all'))

@stories_bp.route("/highlights")
@login_required
def highlights():
    """View user's story highlights"""
    highlights = Story.query.filter_by(
        user_id=current_user.id,
        is_highlight=True
    ).order_by(Story.created_at.desc()).all()
    
    # Group by highlight title
    highlights_by_title = {}
    for story in highlights:
        title = story.highlight_title or 'Highlights'
        if title not in highlights_by_title:
            highlights_by_title[title] = []
        highlights_by_title[title].append(story)
    
    return render_template("stories/highlights.html", highlights_by_title=highlights_by_title)

@stories_bp.route("/<int:story_id>/viewers")
@login_required
def viewers(story_id):
    """Get list of story viewers"""
    story = Story.query.get_or_404(story_id)
    
    if story.user_id != current_user.id:
        flash('You can only view viewers for your own stories.', 'error')
        return redirect(url_for('stories.view_all'))
    
    views = StoryView.query.filter_by(story_id=story_id)\
                           .options(joinedload(StoryView.viewer))\
                           .order_by(StoryView.created_at.desc()).all()
    
    return render_template("stories/viewers.html", story=story, views=views)

@stories_bp.route("/api/feed")
@login_required
def api_feed():
    """API endpoint to get stories feed (for infinite scroll)"""
    # Get users you follow
    following_ids = [f.followed_id for f in current_user.following.all()]
    following_ids.append(current_user.id)
    
    # Get active stories
    stories_query = Story.query.filter(
        Story.user_id.in_(following_ids),
        Story.expires_at > datetime.utcnow()
    ).options(
        joinedload(Story.user)
    ).order_by(Story.created_at.desc())
    
    stories = stories_query.limit(20).all()
    
    # Group by user
    stories_by_user = {}
    for story in stories:
        if story.user_id not in stories_by_user:
            stories_by_user[story.user_id] = {
                'user': {
                    'id': story.user.id,
                    'username': story.user.username,
                    'profile_picture': story.user.profile_picture
                },
                'stories': []
            }
        stories_by_user[story.user_id]['stories'].append({
            'id': story.id,
            'media_url': story.media_url,
            'media_type': story.media_type,
            'created_at': story.created_at.isoformat(),
            'is_viewed': story.is_viewed_by(current_user),
            'view_count': story.view_count()
        })
    
    return jsonify({
        'stories_by_user': list(stories_by_user.values())
    })


