from app.extension import db
from datetime import datetime

class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one bookmark per user per post
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_bookmark'),)
    
    def __repr__(self):
        return f'<Bookmark by User {self.user_id} on Post {self.post_id}>'

