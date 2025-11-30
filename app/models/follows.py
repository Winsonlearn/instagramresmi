from app.extension import db
from datetime import datetime

class Follow(db.Model):
    __tablename__ = "follows"
    
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='accepted', nullable=False)  # 'accepted', 'pending', 'blocked'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Unique constraint: prevent duplicate follows
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),)
    
    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id} status={self.status}>'

