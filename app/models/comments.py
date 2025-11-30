from app.extension import db
from datetime import datetime

class Comment(db.Model):
    __tablename__ = "comments"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, index=True)  # For nested comments
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Self-referential relationship for nested comments
    # parent is many-to-one (uselist=False), so cannot use 'dynamic'
    parent = db.relationship('Comment', remote_side=[id], backref=db.backref('replies', lazy='dynamic'), lazy='select')
    
    def get_replies(self):
        """Get all direct replies to this comment"""
        return Comment.query.filter_by(parent_id=self.id).order_by(Comment.created_at.asc()).all()
    
    def reply_count(self):
        """Get total number of replies"""
        return Comment.query.filter_by(parent_id=self.id).count()
    
    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id}>'

