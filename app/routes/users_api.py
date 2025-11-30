"""
RESTful API endpoints for user management
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, and_

from app.extension import db
from app.models.users import User
from app.models.follows import Follow
from app.models.user_settings import UserSettings
from app.models.blocked_users import BlockedUser
from app.models.notifications import Notification
from app.lib.auth import api_login_required
from app.utils import save_profile_image
import os

users_api = Blueprint("users_api", __name__, url_prefix="/api/users")

@users_api.route("/<int:user_id>", methods=["GET"])
@api_login_required
def get_user(user_id):
    """GET /api/users/:id - Get user profile"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    user = User.query.get_or_404(user_id)
    
    # Check if user is blocked
    if viewer and (viewer.is_blocked(user) or user.is_blocked(viewer)):
        return jsonify({'error': 'User not found'}), 404
    
    # Check if account is active
    if not user.is_active:
        return jsonify({'error': 'User not found'}), 404
    
    is_own_profile = viewer and viewer.id == user.id
    is_following = viewer.is_following(user) if viewer else False
    has_pending = viewer.has_pending_follow_request(user) if viewer else False
    
    # For private accounts, only show limited info to non-followers
    can_view_content = is_own_profile or (not user.is_private) or is_following
    
    response = {
        'id': user.id,
        'username': user.username,
        'fullname': user.fullname,
        'bio': user.bio if can_view_content else None,
        'profile_picture': user.profile_picture,
        'is_verified': user.is_verified,
        'is_private': user.is_private,
        'followers_count': user.get_followers_count(viewer) if can_view_content else None,
        'following_count': user.get_following_count(viewer) if can_view_content else None,
        'is_following': is_following,
        'has_pending_request': has_pending,
        'is_own_profile': is_own_profile,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }
    
    # Only include email for own profile
    if is_own_profile:
        response['email'] = user.email
        response['email_verified'] = user.email_verified
    
    return jsonify(response), 200

@users_api.route("/<int:user_id>", methods=["PUT"])
@api_login_required
def update_user(user_id):
    """PUT /api/users/:id - Update user profile"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer or viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Update fullname
        if 'fullname' in data:
            fullname = data['fullname'].strip()
            if fullname and 2 <= len(fullname) <= 32:
                viewer.fullname = fullname
            else:
                return jsonify({'error': 'Full name must be 2-32 characters'}), 400
        
        # Update bio
        if 'bio' in data:
            bio = data['bio'].strip() if data['bio'] else None
            if bio and len(bio) > 150:
                return jsonify({'error': 'Bio must be 150 characters or less'}), 400
            viewer.bio = bio
        
        # Update privacy setting
        if 'is_private' in data:
            viewer.is_private = bool(data['is_private'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': viewer.id,
                'username': viewer.username,
                'fullname': viewer.fullname,
                'bio': viewer.bio,
                'is_private': viewer.is_private
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'Error updating profile'}), 500

@users_api.route("/<int:user_id>/follow", methods=["POST"])
@api_login_required
def follow_user(user_id):
    """POST /api/users/:id/follow - Follow a user"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get_or_404(user_id)
    
    if viewer.id == user.id:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    
    # Check if blocked
    if viewer.is_blocked(user) or user.is_blocked(viewer):
        return jsonify({'error': 'Cannot follow this user'}), 403
    
    try:
        if viewer.is_following(user):
            return jsonify({'error': 'Already following this user'}), 400
        
        if viewer.has_pending_follow_request(user):
            return jsonify({'error': 'Follow request already pending'}), 400
        
        success = viewer.follow(user)
        
        if success:
            # Create notification if accepted (public account)
            if not user.is_private:
                notification = Notification(
                    user_id=user.id,
                    from_user_id=viewer.id,
                    notification_type='follow'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            follow = viewer.following.filter_by(followed_id=user.id).first()
            return jsonify({
                'message': 'Follow request sent' if user.is_private else 'Following user',
                'status': follow.status if follow else 'pending',
                'is_following': follow.status == 'accepted' if follow else False
            }), 200
        else:
            return jsonify({'error': 'Error processing follow'}), 500
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Follow error: {str(e)}")
        return jsonify({'error': 'Error processing follow'}), 500

@users_api.route("/<int:user_id>/unfollow", methods=["DELETE"])
@api_login_required
def unfollow_user(user_id):
    """DELETE /api/users/:id/unfollow - Unfollow a user"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get_or_404(user_id)
    
    if viewer.id == user.id:
        return jsonify({'error': 'Cannot unfollow yourself'}), 400
    
    try:
        success = viewer.unfollow(user)
        
        if success:
            db.session.commit()
            return jsonify({'message': 'Unfollowed successfully'}), 200
        else:
            return jsonify({'error': 'Not following this user'}), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unfollow error: {str(e)}")
        return jsonify({'error': 'Error processing unfollow'}), 500

@users_api.route("/<int:user_id>/followers", methods=["GET"])
@api_login_required
def get_followers(user_id):
    """GET /api/users/:id/followers - Get followers list with pagination"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    user = User.query.get_or_404(user_id)
    
    # Check permissions
    is_own_profile = viewer and viewer.id == user.id
    is_following = viewer.is_following(user) if viewer else False
    can_view = is_own_profile or (not user.is_private) or is_following
    
    if not can_view:
        return jsonify({'error': 'Cannot view followers of private account'}), 403
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Max 100 per page
    
    # Get followers (only accepted, exclude blocked)
    query = user.followers.filter_by(status='accepted')
    
    if viewer:
        blocked_ids = [b.blocked_id for b in BlockedUser.query.filter_by(blocker_id=viewer.id).all()]
        if blocked_ids:
            query = query.filter(~Follow.follower_id.in_(blocked_ids))
    
    pagination = query.order_by(Follow.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    followers = []
    for follow in pagination.items:
        follower = User.query.get(follow.follower_id)
        if follower and follower.is_active:
            followers.append({
                'id': follower.id,
                'username': follower.username,
                'fullname': follower.fullname,
                'profile_picture': follower.profile_picture,
                'is_verified': follower.is_verified,
                'is_following': viewer.is_following(follower) if viewer else False,
                'is_own_profile': viewer.id == follower.id if viewer else False
            })
    
    return jsonify({
        'followers': followers,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200

@users_api.route("/<int:user_id>/following", methods=["GET"])
@api_login_required
def get_following(user_id):
    """GET /api/users/:id/following - Get following list with pagination"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    user = User.query.get_or_404(user_id)
    
    # Check permissions
    is_own_profile = viewer and viewer.id == user.id
    is_following = viewer.is_following(user) if viewer else False
    can_view = is_own_profile or (not user.is_private) or is_following
    
    if not can_view:
        return jsonify({'error': 'Cannot view following of private account'}), 403
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Max 100 per page
    
    # Get following (only accepted, exclude blocked)
    query = user.following.filter_by(status='accepted')
    
    if viewer:
        blocked_ids = [b.blocked_id for b in BlockedUser.query.filter_by(blocker_id=viewer.id).all()]
        if blocked_ids:
            query = query.filter(~Follow.followed_id.in_(blocked_ids))
    
    pagination = query.order_by(Follow.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    following = []
    for follow in pagination.items:
        followed = User.query.get(follow.followed_id)
        if followed and followed.is_active:
            following.append({
                'id': followed.id,
                'username': followed.username,
                'fullname': followed.fullname,
                'profile_picture': followed.profile_picture,
                'is_verified': followed.is_verified,
                'is_following': viewer.is_following(followed) if viewer else False,
                'is_own_profile': viewer.id == followed.id if viewer else False
            })
    
    return jsonify({
        'following': following,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200

@users_api.route("/<int:user_id>/remove-follower", methods=["DELETE"])
@api_login_required
def remove_follower(user_id):
    """DELETE /api/users/:id/remove-follower - Remove a follower"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Can only remove your own followers
    if viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    follower_id = data.get('follower_id') if data else None
    
    if not follower_id:
        return jsonify({'error': 'follower_id is required'}), 400
    
    follower = User.query.get_or_404(follower_id)
    
    try:
        success = viewer.remove_follower(follower)
        
        if success:
            db.session.commit()
            return jsonify({'message': 'Follower removed successfully'}), 200
        else:
            return jsonify({'error': 'User is not a follower'}), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Remove follower error: {str(e)}")
        return jsonify({'error': 'Error removing follower'}), 500

@users_api.route("/<int:user_id>/follow-requests", methods=["GET"])
@api_login_required
def get_follow_requests(user_id):
    """GET /api/users/:id/follow-requests - Get pending follow requests (own profile only)"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer or viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get pending follow requests
    pending = viewer.followers.filter_by(status='pending').all()
    
    requests = []
    for follow in pending:
        requester = User.query.get(follow.follower_id)
        if requester and requester.is_active:
            requests.append({
                'id': requester.id,
                'username': requester.username,
                'fullname': requester.fullname,
                'profile_picture': requester.profile_picture,
                'is_verified': requester.is_verified,
                'requested_at': follow.created_at.isoformat() if follow.created_at else None
            })
    
    return jsonify({'follow_requests': requests}), 200

@users_api.route("/<int:user_id>/follow-requests/<int:requester_id>/accept", methods=["POST"])
@api_login_required
def accept_follow_request(user_id, requester_id):
    """POST /api/users/:id/follow-requests/:requester_id/accept - Accept follow request"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer or viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    requester = User.query.get_or_404(requester_id)
    
    try:
        success = viewer.accept_follow_request(requester)
        
        if success:
            # Create notification
            notification = Notification(
                user_id=requester.id,
                from_user_id=viewer.id,
                notification_type='follow'
            )
            db.session.add(notification)
            db.session.commit()
            
            return jsonify({'message': 'Follow request accepted'}), 200
        else:
            return jsonify({'error': 'Follow request not found'}), 404
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Accept follow request error: {str(e)}")
        return jsonify({'error': 'Error accepting follow request'}), 500

@users_api.route("/<int:user_id>/follow-requests/<int:requester_id>/decline", methods=["POST"])
@api_login_required
def decline_follow_request(user_id, requester_id):
    """POST /api/users/:id/follow-requests/:requester_id/decline - Decline follow request"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer or viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    requester = User.query.get_or_404(requester_id)
    
    try:
        success = viewer.decline_follow_request(requester)
        
        if success:
            db.session.commit()
            return jsonify({'message': 'Follow request declined'}), 200
        else:
            return jsonify({'error': 'Follow request not found'}), 404
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Decline follow request error: {str(e)}")
        return jsonify({'error': 'Error declining follow request'}), 500

@users_api.route("/suggested", methods=["GET"])
@api_login_required
def get_suggested_users():
    """GET /api/users/suggested - Get suggested users to follow"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)  # Max 50
    
    # Get users that viewer is not following, not blocked, and active
    following_ids = [f.followed_id for f in viewer.following.all()]
    blocked_ids = [b.blocked_id for b in BlockedUser.query.filter_by(blocker_id=viewer.id).all()]
    
    exclude_ids = following_ids + blocked_ids + [viewer.id]
    
    # Get users followed by people you follow (suggestions)
    suggested = db.session.query(User).filter(
        User.id.notin_(exclude_ids),
        User.is_active == True
    ).order_by(User.created_at.desc()).limit(limit).all()
    
    users = []
    for user in suggested:
        users.append({
            'id': user.id,
            'username': user.username,
            'fullname': user.fullname,
            'profile_picture': user.profile_picture,
            'is_verified': user.is_verified,
            'is_private': user.is_private
        })
    
    return jsonify({'suggested_users': users}), 200

@users_api.route("/<int:user_id>/block", methods=["POST"])
@api_login_required
def block_user(user_id):
    """POST /api/users/:id/block - Block a user"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get_or_404(user_id)
    
    if viewer.id == user.id:
        return jsonify({'error': 'Cannot block yourself'}), 400
    
    try:
        success = viewer.block_user(user)
        
        if success:
            db.session.commit()
            return jsonify({'message': 'User blocked successfully'}), 200
        else:
            return jsonify({'error': 'User already blocked'}), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Block user error: {str(e)}")
        return jsonify({'error': 'Error blocking user'}), 500

@users_api.route("/<int:user_id>/unblock", methods=["POST"])
@api_login_required
def unblock_user(user_id):
    """POST /api/users/:id/unblock - Unblock a user"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get_or_404(user_id)
    
    try:
        success = viewer.unblock_user(user)
        
        if success:
            db.session.commit()
            return jsonify({'message': 'User unblocked successfully'}), 200
        else:
            return jsonify({'error': 'User not blocked'}), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unblock user error: {str(e)}")
        return jsonify({'error': 'Error unblocking user'}), 500

@users_api.route("/<int:user_id>/avatar", methods=["POST"])
@api_login_required
def upload_avatar(user_id):
    """POST /api/users/:id/avatar - Upload profile picture"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer or viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['profile_picture']
    if not file or not file.filename:
        return jsonify({'error': 'No file provided'}), 400
    
    try:
        filename, error = save_profile_image(file, viewer.id)
        
        if error:
            return jsonify({'error': error}), 400
        
        if filename:
            # Delete old profile picture
            if viewer.profile_picture and viewer.profile_picture != 'default_profile.png':
                old_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    'profiles',
                    viewer.profile_picture
                )
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass
            
            viewer.profile_picture = filename
            db.session.commit()
            
            return jsonify({
                'message': 'Profile picture updated',
                'profile_picture': filename
            }), 200
        else:
            return jsonify({'error': 'Error uploading image'}), 500
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload avatar error: {str(e)}")
        return jsonify({'error': 'Error uploading avatar'}), 500

@users_api.route("/settings", methods=["GET", "PUT"])
@api_login_required
def user_settings():
    """GET/PUT /api/users/settings - Get or update user settings"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Get or create settings
    settings = UserSettings.query.filter_by(user_id=viewer.id).first()
    if not settings:
        settings = UserSettings(user_id=viewer.id)
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'GET':
        return jsonify({
            'is_private': settings.is_private,
            'show_email': settings.show_email,
            'allow_messages': settings.allow_messages,
            'email_notifications': settings.email_notifications,
            'push_notifications': settings.push_notifications,
            'follow_notifications': settings.follow_notifications,
            'like_notifications': settings.like_notifications,
            'comment_notifications': settings.comment_notifications,
            'two_factor_enabled': settings.two_factor_enabled
        }), 200
    
    # PUT request
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        if 'is_private' in data:
            settings.is_private = bool(data['is_private'])
            viewer.is_private = settings.is_private  # Sync with user model
        
        if 'show_email' in data:
            settings.show_email = bool(data['show_email'])
        
        if 'allow_messages' in data:
            settings.allow_messages = bool(data['allow_messages'])
        
        if 'email_notifications' in data:
            settings.email_notifications = bool(data['email_notifications'])
        
        if 'push_notifications' in data:
            settings.push_notifications = bool(data['push_notifications'])
        
        if 'follow_notifications' in data:
            settings.follow_notifications = bool(data['follow_notifications'])
        
        if 'like_notifications' in data:
            settings.like_notifications = bool(data['like_notifications'])
        
        if 'comment_notifications' in data:
            settings.comment_notifications = bool(data['comment_notifications'])
        
        if 'two_factor_enabled' in data:
            settings.two_factor_enabled = bool(data['two_factor_enabled'])
        
        db.session.commit()
        
        return jsonify({'message': 'Settings updated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update settings error: {str(e)}")
        return jsonify({'error': 'Error updating settings'}), 500

@users_api.route("/<int:user_id>/deactivate", methods=["POST"])
@api_login_required
def deactivate_account(user_id):
    """POST /api/users/:id/deactivate - Deactivate account"""
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    if not viewer or viewer.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json() or {}
    password = data.get('password', '')
    
    # Verify password
    from werkzeug.security import check_password_hash
    if not password or not check_password_hash(viewer.password, password):
        return jsonify({'error': 'Invalid password'}), 401
    
    try:
        viewer.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Account deactivated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Deactivate account error: {str(e)}")
        return jsonify({'error': 'Error deactivating account'}), 500


@users_api.route("/search", methods=["GET"])
@api_login_required
def search_users():
    """GET /api/users/search?q=query - Search users"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    viewer_id = getattr(request, 'current_user_id', current_user.id if current_user.is_authenticated else None)
    viewer = User.query.get(viewer_id) if viewer_id else None
    
    # Search by username or fullname
    users = User.query.filter(
        and_(
            User.is_active == True,
            or_(
                User.username.ilike(f'%{query}%'),
                User.fullname.ilike(f'%{query}%')
            )
        )
    ).limit(20).all()
    
    # Filter out blocked users
    if viewer:
        users = [u for u in users if u.id != viewer.id and not viewer.is_blocked(u) and not u.is_blocked(viewer)]
    
    results = []
    for user in users[:10]:  # Limit to 10 results
        results.append({
            'id': user.id,
            'username': user.username,
            'fullname': user.fullname,
            'profile_picture': user.profile_picture,
            'is_verified': user.is_verified,
            'is_private': user.is_private
        })
    
    return jsonify(results)

