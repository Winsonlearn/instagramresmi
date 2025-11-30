from app.extension import db
from datetime import datetime

class UserSettings(db.Model):
    __tablename__ = "user_settings"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    
    # Privacy settings
    is_private = db.Column(db.Boolean, default=False, nullable=False)
    show_email = db.Column(db.Boolean, default=False, nullable=False)
    allow_messages = db.Column(db.Boolean, default=True, nullable=False)
    
    # Notification settings
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)
    follow_notifications = db.Column(db.Boolean, default=True, nullable=False)
    like_notifications = db.Column(db.Boolean, default=True, nullable=False)
    comment_notifications = db.Column(db.Boolean, default=True, nullable=False)
    
    # Account settings
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='settings', uselist=False)
    
    def __repr__(self):
        return f'<UserSettings user_id={self.user_id}>'


