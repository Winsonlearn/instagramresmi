from app.extension import db
from datetime import datetime

class StoryView(db.Model):
    __tablename__ = "story_views"
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, index=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Unique constraint: one view per user per story (to prevent duplicate views)
    __table_args__ = (db.UniqueConstraint('story_id', 'viewer_id', name='unique_story_viewer'),)
    
    # Relationships
    viewer = db.relationship('User', backref='story_views', lazy='select')
    
    def __repr__(self):
        return f'<StoryView {self.id} - Story {self.story_id} by User {self.viewer_id}>'


