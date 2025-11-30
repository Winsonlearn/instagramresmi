from app.extension import db
from datetime import datetime, timedelta

class Story(db.Model):
    __tablename__ = "stories"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    media_url = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(10), default='image', nullable=False)  # 'image' or 'video'
    text_overlay = db.Column(db.Text, nullable=True)  # JSON string for text/stickers/filters
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_highlight = db.Column(db.Boolean, default=False, index=True)  # Saved to highlights
    highlight_title = db.Column(db.String(100), nullable=True)  # Title for highlight
    
    # Relationships
    user = db.relationship('User', backref='stories', lazy='select')
    views = db.relationship('StoryView', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_expired(self):
        """Check if story has expired"""
        return datetime.utcnow() > self.expires_at
    
    def view_count(self):
        """Get total number of views"""
        return self.views.count()
    
    def is_viewed_by(self, user):
        """Check if story is viewed by user"""
        if user is None or not user.is_authenticated:
            return False
        return self.views.filter_by(viewer_id=user.id).first() is not None
    
    @staticmethod
    def create_expires_at():
        """Create expiration time (24 hours from now)"""
        return datetime.utcnow() + timedelta(hours=24)
    
    def __repr__(self):
        return f'<Story {self.id} by User {self.user_id}>'


