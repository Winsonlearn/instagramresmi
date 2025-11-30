from app.extension import db
from datetime import datetime

class BlockedUser(db.Model):
    __tablename__ = "blocked_users"
    
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    blocked_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Unique constraint: prevent duplicate blocks
    __table_args__ = (db.UniqueConstraint('blocker_id', 'blocked_id', name='unique_block'),)
    
    def __repr__(self):
        return f'<BlockedUser {self.blocker_id} blocked {self.blocked_id}>'


