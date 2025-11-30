from app.extension import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = "notifications"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    notification_type = db.Column(db.String(20), nullable=False, index=True)  # 'like', 'comment', 'follow', 'message', 'mention'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=True, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=True, index=True)
    read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    from_user = db.relationship('User', foreign_keys=[from_user_id])
    post = db.relationship('Post', backref='notifications')
    comment = db.relationship('Comment', backref='notifications')
    conversation = db.relationship('Conversation', backref='notifications')
    message = db.relationship('Message', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id} type={self.notification_type} for user {self.user_id}>'

