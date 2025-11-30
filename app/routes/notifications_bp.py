from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.extension import db
from app.models.notifications import Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notifications_bp.route("/")
@login_required
def view():
    """View all notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                     .options(joinedload(Notification.from_user))\
                                     .options(joinedload(Notification.post))\
                                     .options(joinedload(Notification.comment))\
                                     .options(joinedload(Notification.conversation))\
                                     .order_by(Notification.created_at.desc())\
                                     .limit(50).all()
    
    return render_template("notifications/view.html", notifications=notifications)


@notifications_bp.route("/api", methods=["GET"])
@login_required
def api_list():
    """API endpoint to get notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                     .options(joinedload(Notification.from_user))\
                                     .options(joinedload(Notification.post))\
                                     .options(joinedload(Notification.comment))\
                                     .options(joinedload(Notification.conversation))\
                                     .order_by(Notification.created_at.desc())\
                                     .limit(50).all()
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'from_user': {
                'id': notif.from_user.id if notif.from_user else None,
                'username': notif.from_user.username if notif.from_user else None,
                'profile_picture': notif.from_user.profile_picture if notif.from_user else None
            } if notif.from_user else None,
            'post_id': notif.post_id,
            'comment_id': notif.comment_id,
            'conversation_id': notif.conversation_id,
            'read': notif.read,
            'created_at': notif.created_at.isoformat()
        })
    
    return jsonify(notifications_data)

@notifications_bp.route("/count", methods=["GET"])
@login_required
def count():
    """Get count of unread notifications"""
    count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify({'count': count})

@notifications_bp.route("/mark-read/<int:notification_id>", methods=["POST"])
@login_required
def mark_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        notification.read = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Error updating notification'}), 500

@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    from flask import redirect, url_for, flash
    
    # CSRF validation is handled by Flask-WTF automatically if WTF_CSRF_ENABLED is True
    # For POST requests without forms, we can skip explicit validation if needed
    # or use validate_csrf() if custom validation is required
    
    try:
        updated = Notification.query.filter_by(user_id=current_user.id, read=False)\
                                   .update({Notification.read: True})
        db.session.commit()
        
        if updated > 0:
            flash(f'Marked {updated} notification(s) as read.', 'success')
        else:
            flash('All notifications are already read.', 'info')
            
        return redirect(url_for('notifications.view'))
    except Exception as e:
        db.session.rollback()
        flash('Error updating notifications. Please try again.', 'error')
        return redirect(url_for('notifications.view'))

