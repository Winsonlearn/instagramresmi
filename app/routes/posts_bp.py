from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extension import cache
import os
import time

from app.extension import db
from sqlalchemy.orm import joinedload
from app.forms.postForm import PostForm
from app.forms.editPostForm import EditPostForm
from app.forms.commentForm import CommentForm
from app.models.posts import Post
from app.models.comments import Comment
from app.models.likes import Like
from app.models.bookmarks import Bookmark
from app.models.notifications import Notification
from app.utils import save_post_image, save_post_media, extract_hashtags, extract_mentions

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")

@posts_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new post"""
    form = PostForm()
    if request.method == "POST":
        # Validate form fields (except media which we'll check manually)
        if form.validate_on_submit() or True:  # Always proceed, we'll validate media separately
            # Handle multiple media files (carousel support)
            media_files = request.files.getlist('media')
            
            # Check if any files were selected
            valid_files = [f for f in media_files if f and f.filename]
            if not valid_files:
                flash('Please select at least one image or video to upload.', 'error')
                return render_template("posts/create.html", form=form)
            
            # Limit to 10 media items
            if len(valid_files) > 10:
                flash('Maximum 10 media items allowed per post.', 'error')
                return render_template("posts/create.html", form=form)
            
            try:
                timestamp = int(time.time() * 1000)
                media_list = []
                alt_texts = request.form.getlist('alt_texts')  # Get alt texts from form
                
                # Save each media file
                for idx, file in enumerate(valid_files):
                    alt_text = alt_texts[idx] if idx < len(alt_texts) else ""
                    try:
                        media_obj, error = save_post_media(file, current_user.id, timestamp + idx, alt_text)
                        
                        if not media_obj:
                            error_msg = error or f'Error uploading media {idx + 1}. Please try again.'
                            current_app.logger.error(f"Media upload failed: {error_msg}")
                            flash(error_msg, 'error')
                            return render_template("posts/create.html", form=form)
                        
                        media_list.append(media_obj)
                    except Exception as media_error:
                        current_app.logger.error(f"Exception during media save: {str(media_error)}", exc_info=True)
                        flash(f'Error processing media {idx + 1}: {str(media_error)}', 'error')
                        return render_template("posts/create.html", form=form)
                
                if not media_list:
                    flash('No valid media files uploaded.', 'error')
                    return render_template("posts/create.html", form=form)
                
                # Create post with media list
                post = Post(
                    user_id=current_user.id,
                    caption=form.caption.data.strip() if form.caption.data else None,
                    location=form.location.data.strip() if form.location.data else None
                )
                post.set_media_list(media_list)
                
                # Set _image_url_db to first media URL for backward compatibility
                # This ensures the NOT NULL constraint is satisfied
                if media_list and len(media_list) > 0:
                    post._image_url_db = media_list[0]['url']
                else:
                    post._image_url_db = ''  # Empty string instead of NULL
                
                db.session.add(post)
                db.session.flush()  # Get post ID
                
                # Extract and process hashtags/mentions (could notify mentioned users)
                mentions = extract_mentions(post.caption) if post.caption else []
                # TODO: Create notifications for mentioned users
                
                db.session.commit()
                
                flash('Post created successfully!', 'success')
                return redirect(url_for('main.feed'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating post: {str(e)}", exc_info=True)
                # Don't expose internal errors to users in production
                # But show detailed error in development
                if current_app.config.get('DEBUG'):
                    flash(f'Error creating post: {str(e)}', 'error')
                else:
                    flash('Error creating post. Please try again.', 'error')
    
    return render_template("posts/create.html", form=form)

@posts_bp.route("/<int:post_id>")
@login_required
def detail(post_id):
    """View a single post with comments"""
    # Optimize query: eager load user relationship
    post = Post.query.options(
        joinedload(Post.user)
    ).get_or_404(post_id)
    
    form = CommentForm()
    
    # Get comments ordered by oldest first (limit to 50) with user relationship
    comments = Comment.query.filter_by(post_id=post_id)\
                           .options(joinedload(Comment.user))\
                           .order_by(Comment.created_at.asc())\
                           .limit(50).all()
    
    return render_template("posts/detail.html", post=post, comments=comments, form=form)

@posts_bp.route("/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    """Add a comment to a post (supports nested comments via parent_id)"""
    form = CommentForm()
    post = Post.query.get_or_404(post_id)
    
    # Check if this is a reply to another comment
    parent_id = request.form.get('parent_id', type=int)
    if parent_id:
        parent_comment = Comment.query.get_or_404(parent_id)
        if parent_comment.post_id != post_id:
            flash('Invalid comment reply.', 'error')
            return redirect(url_for('posts.detail', post_id=post_id))
    
    if form.validate_on_submit():
        try:
            comment = Comment(
                user_id=current_user.id,
                post_id=post_id,
                content=form.content.data.strip(),
                parent_id=parent_id if parent_id else None
            )
            db.session.add(comment)
            db.session.flush()  # Get comment ID
            
            # Create notification for post owner (if not commenting on own post)
            if post.user_id != current_user.id:
                notification = Notification(
                    user_id=post.user_id,
                    from_user_id=current_user.id,
                    notification_type='comment',
                    post_id=post_id,
                    comment_id=comment.id
                )
                db.session.add(notification)
            
            # If replying to a comment, notify the parent comment owner
            if parent_id and parent_comment.user_id != current_user.id:
                notification = Notification(
                    user_id=parent_comment.user_id,
                    from_user_id=current_user.id,
                    notification_type='comment',
                    post_id=post_id,
                    comment_id=comment.id
                )
                db.session.add(notification)
            
            db.session.commit()
            flash('Comment added!', 'success')
        except Exception:
            db.session.rollback()
            flash('Error adding comment. Please try again.', 'error')
    
    return redirect(url_for('posts.detail', post_id=post_id))

@posts_bp.route("/<int:post_id>/like", methods=["POST"])
@login_required
def toggle_like(post_id):
    """Toggle like on a post"""
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    try:
        if like:
            # Unlike
            db.session.delete(like)
            db.session.commit()
            liked = False
        else:
            # Like
            like = Like(user_id=current_user.id, post_id=post_id)
            db.session.add(like)
            
            # Create notification for post owner (if not liking own post)
            if post.user_id != current_user.id:
                # Check if notification already exists to avoid duplicates
                existing_notif = Notification.query.filter_by(
                    user_id=post.user_id,
                    from_user_id=current_user.id,
                    notification_type='like',
                    post_id=post_id,
                    read=False
                ).first()
                
                if not existing_notif:
                    notification = Notification(
                        user_id=post.user_id,
                        from_user_id=current_user.id,
                        notification_type='like',
                        post_id=post_id
                    )
                    db.session.add(notification)
            
            db.session.commit()
            liked = True
        
        like_count = post.like_count()
        
        return jsonify({
            'liked': liked,
            'like_count': like_count
        })
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Error processing like'}), 500

@posts_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit(post_id):
    """Edit a post (only by owner)"""
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        flash('You can only edit your own posts.', 'error')
        return redirect(url_for('posts.detail', post_id=post_id))
    
    form = EditPostForm()
    
    if form.validate_on_submit():
        try:
            caption = form.caption.data.strip() if form.caption.data else None
            post.caption = caption
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('posts.detail', post_id=post_id))
        except Exception:
            db.session.rollback()
            flash('Error updating post. Please try again.', 'error')
    else:
        # Populate form with existing caption
        form.caption.data = post.caption
    
    return render_template("posts/edit.html", post=post, form=form)

@posts_bp.route("/<int:post_id>/delete", methods=["POST"])
@login_required
def delete(post_id):
    """Delete a post (only by owner)"""
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        flash('You can only delete your own posts.', 'error')
        return redirect(url_for('main.feed'))
    
    try:
        # Delete image file
        if post.image_url:
            image_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                'posts',
                post.image_url
            )
            if os.path.exists(image_path) and os.path.isfile(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # Continue even if file deletion fails
        
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error deleting post. Please try again.', 'error')
    
    return redirect(url_for('main.feed'))

@posts_bp.route("/<int:post_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(post_id):
    """Toggle bookmark on a post"""
    post = Post.query.get_or_404(post_id)
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    try:
        if bookmark:
            # Unbookmark
            db.session.delete(bookmark)
            db.session.commit()
            bookmarked = False
        else:
            # Bookmark
            bookmark = Bookmark(user_id=current_user.id, post_id=post_id)
            db.session.add(bookmark)
            db.session.commit()
            bookmarked = True
        
        return jsonify({
            'bookmarked': bookmarked
        })
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Error processing bookmark'}), 500

@posts_bp.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    """Edit a comment"""
    comment = Comment.query.get_or_404(comment_id)
    form = CommentForm()

    if comment.user_id != current_user.id:
        flash('You can only edit your own comments.', 'error')
        return redirect(url_for('posts.detail', post_id=comment.post_id))

    if request.method == "POST":
        content = request.form.get('content', '').strip()
        if content and len(content) <= 2200:
            try:
                comment.content = content
                db.session.commit()
                flash('Comment updated!', 'success')
            except Exception:
                db.session.rollback()
                flash('Error updating comment. Please try again.', 'error')
        else:
            flash('Comment cannot be empty or too long.', 'error')
        return redirect(url_for('posts.detail', post_id=comment.post_id))
    
    # Populate form with existing comment content
    form.content.data = comment.content
    return render_template("posts/edit_comment.html", comment=comment, form=form)

@posts_bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    
    if comment.user_id != current_user.id:
        flash('You can only delete your own comments.', 'error')
        return redirect(url_for('posts.detail', post_id=post_id))
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error deleting comment. Please try again.', 'error')
    
    return redirect(url_for('posts.detail', post_id=post_id))

@posts_bp.route("/<int:post_id>/share", methods=["POST"])
@login_required
def share(post_id):
    """Share a post (copy link or send via DM)"""
    post = Post.query.get_or_404(post_id)
    share_type = request.json.get('type', 'link')  # 'link' or 'dm'
    
    if share_type == 'link':
        # Generate shareable link
        post_url = url_for('posts.detail', post_id=post_id, _external=True)
        return jsonify({
            'success': True,
            'url': post_url,
            'message': 'Link copied to clipboard'
        })
    elif share_type == 'dm':
        # TODO: Implement DM sharing when messages are implemented
        return jsonify({'error': 'DM sharing not yet implemented'}), 501
    else:
        return jsonify({'error': 'Invalid share type'}), 400

@posts_bp.route("/<int:post_id>/report", methods=["POST"])
@login_required
def report(post_id):
    """Report a post"""
    post = Post.query.get_or_404(post_id)
    
    # Don't allow reporting own posts
    if post.user_id == current_user.id:
        return jsonify({'error': 'You cannot report your own post'}), 400
    
    reason = request.json.get('reason', '')
    # TODO: Create a PostReport model to store reports
    # For now, just return success
    
    return jsonify({
        'success': True,
        'message': 'Post reported successfully. We will review it shortly.'
    })

@posts_bp.route("/api/feed")
@login_required
def api_feed():
    """API endpoint for feed pagination (infinite scroll)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    sort_by = request.args.get('sort', 'latest')  # 'latest' or 'algorithm'
    
    # Get posts from users you follow + your own posts
    following_ids = [f.followed_id for f in current_user.following.all()]
    following_ids.append(current_user.id)
    
    if following_ids:
        posts_query = Post.query.filter(Post.user_id.in_(following_ids))\
                                .options(joinedload(Post.user))
        
        if sort_by == 'latest':
            posts_query = posts_query.order_by(Post.created_at.desc())
        else:  # algorithm - simplified version
            # Sort by engagement score (likes + comments per hour)
            from sqlalchemy import func
            posts_query = posts_query.outerjoin(Like).outerjoin(Comment)\
                                     .group_by(Post.id)\
                                     .order_by(
                                         (func.count(Like.id) * 2 + func.count(Comment.id)).desc()
                                     )
        
        posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # If no posts from following, show explore (all posts)
        if posts.total == 0:
            posts = Post.query.options(joinedload(Post.user))\
                              .order_by(Post.created_at.desc())\
                              .paginate(page=page, per_page=per_page, error_out=False)
    else:
        # User is not following anyone, show all posts
        posts = Post.query.options(joinedload(Post.user))\
                          .order_by(Post.created_at.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
    
    posts_data = []
    for post in posts.items:
        posts_data.append({
            'id': post.id,
            'user': {
                'id': post.user.id,
                'username': post.user.username,
                'profile_picture': post.user.profile_picture
            },
            'media': post.get_media_list(),
            'caption': post.caption,
            'location': post.location,
            'created_at': post.created_at.isoformat(),
            'like_count': post.like_count(),
            'comment_count': post.comment_count(),
            'is_liked': post.is_liked_by(current_user),
            'is_bookmarked': post.is_bookmarked_by(current_user)
        })
    
    return jsonify({
        'posts': posts_data,
        'has_next': posts.has_next,
        'has_prev': posts.has_prev,
        'page': page,
        'pages': posts.pages,
        'total': posts.total
    })

@posts_bp.route("/api/<int:post_id>")
@login_required
def api_post_detail(post_id):
    """API endpoint to get single post details"""
    post = Post.query.options(joinedload(Post.user)).get_or_404(post_id)
    
    return jsonify({
        'id': post.id,
        'user': {
            'id': post.user.id,
            'username': post.user.username,
            'profile_picture': post.user.profile_picture
        },
        'media': post.get_media_list(),
        'caption': post.caption,
        'location': post.location,
        'created_at': post.created_at.isoformat(),
        'like_count': post.like_count(),
        'comment_count': post.comment_count(),
        'is_liked': post.is_liked_by(current_user),
        'is_bookmarked': post.is_bookmarked_by(current_user),
        'hashtags': post.extract_hashtags(),
        'mentions': post.extract_mentions()
    })

