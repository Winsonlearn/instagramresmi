from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
import os

from app.extension import db
from app.models.users import User
from app.models.posts import Post
from app.models.follows import Follow
from app.models.notifications import Notification
from app.utils import save_profile_image

profiles_bp = Blueprint("profiles", __name__, url_prefix="/profile")

@profiles_bp.route("/<username>")
@login_required
def view(username):
    """View a user's profile"""
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get user's posts ordered by newest first (already has user via backref)
    posts = Post.query.filter_by(user_id=user.id)\
                     .order_by(Post.created_at.desc())\
                     .all()
    
    # Get follow stats
    following_count = user.following.count()
    followers_count = user.followers.count()
    
    # Check if current user is following this user
    is_following = current_user.is_following(user) if current_user.is_authenticated else False
    is_own_profile = current_user.id == user.id
    
    return render_template(
        "profiles/view.html",
        profile_user=user,
        posts=posts,
        following_count=following_count,
        followers_count=followers_count,
        is_following=is_following,
        is_own_profile=is_own_profile
    )

@profiles_bp.route("/<username>/follow", methods=["POST"])
@login_required
def follow(username):
    """Follow/unfollow a user"""
    user = User.query.filter_by(username=username).first_or_404()
    
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot follow yourself'}), 400
    
    try:
        if current_user.is_following(user):
            current_user.unfollow(user)
            is_following = False
            db.session.commit()
        else:
            current_user.follow(user)
            is_following = True
            
            # Create notification for followed user
            notification = Notification(
                user_id=user.id,
                from_user_id=current_user.id,
                notification_type='follow'
            )
            db.session.add(notification)
            db.session.commit()
        
        followers_count = user.followers.count()
        
        return jsonify({
            'is_following': is_following,
            'followers_count': followers_count
        })
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Error processing follow'}), 500

@profiles_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Edit own profile"""
    if request.method == "POST":
        try:
            # Update profile with input validation
            fullname = request.form.get('fullname', '').strip()
            if fullname and len(fullname) <= 32:
                current_user.fullname = fullname
            
            bio = request.form.get('bio', '').strip()
            if bio:
                if len(bio) <= 150:
                    current_user.bio = bio
                else:
                    flash('Bio must be 150 characters or less.', 'error')
                    return render_template("profiles/edit.html")
            else:
                current_user.bio = None
            
            # Handle profile picture upload
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename:
                    filename, error = save_profile_image(file, current_user.id)
                    if filename:
                        # Delete old profile picture if exists
                        if current_user.profile_picture and current_user.profile_picture != 'default_profile.png':
                            old_path = os.path.join(
                                current_app.config['UPLOAD_FOLDER'],
                                'profiles',
                                current_user.profile_picture
                            )
                            if os.path.exists(old_path) and os.path.isfile(old_path):
                                try:
                                    os.remove(old_path)
                                except OSError:
                                    pass
                        
                        current_user.profile_picture = filename
                    elif error:
                        flash(error, 'error')
                        return render_template("profiles/edit.html")
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profiles.view', username=current_user.username))
        except Exception:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    return render_template("profiles/edit.html")

@profiles_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """User settings page"""
    if request.method == "POST":
        action = request.form.get('action')
        
        if action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            from werkzeug.security import check_password_hash, generate_password_hash
            
            if not old_password or not check_password_hash(current_user.password, old_password):
                flash('Current password is incorrect.', 'error')
            elif not new_password or len(new_password) < 8:
                flash('Password must be at least 8 characters.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            else:
                try:
                    current_user.password = generate_password_hash(new_password)
                    db.session.commit()
                    flash('Password changed successfully!', 'success')
                except Exception:
                    db.session.rollback()
                    flash('Error changing password. Please try again.', 'error')
        
        return redirect(url_for('profiles.settings'))
    
    return render_template("profiles/settings.html")

