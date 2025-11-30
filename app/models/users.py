from app.extension import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    fullname = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True, default='default_profile.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Authentication & Verification
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # Blue checkmark
    is_private = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Account deactivation
    email_verification_token = db.Column(db.String(100), nullable=True, index=True)
    password_reset_token = db.Column(db.String(100), nullable=True, index=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    # Posts created by this user
    posts = db.relationship('Post', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Follow relationships
    # Users this user follows (following)
    following = db.relationship(
        'Follow',
        foreign_keys='Follow.follower_id',
        backref='follower',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    # Users following this user (followers)
    followers = db.relationship(
        'Follow',
        foreign_keys='Follow.followed_id',
        backref='followed',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Comments and likes relationships
    comments = db.relationship('Comment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_following(self, user):
        """Check if this user is following another user (accepted status)"""
        follow = self.following.filter_by(followed_id=user.id).first()
        return follow is not None and follow.status == 'accepted'
    
    def has_pending_follow_request(self, user):
        """Check if there's a pending follow request"""
        follow = self.following.filter_by(followed_id=user.id).first()
        return follow is not None and follow.status == 'pending'
    
    def follow(self, user):
        """Follow a user - creates pending request if private account (does not commit)"""
        if self.id == user.id:
            return False  # Cannot follow yourself
        
        existing_follow = self.following.filter_by(followed_id=user.id).first()
        if existing_follow:
            return False
        
        from app.models.follows import Follow
        # If user has private account, create pending request, else accepted
        status = 'pending' if user.is_private else 'accepted'
        follow = Follow(follower_id=self.id, followed_id=user.id, status=status)
        db.session.add(follow)
        return True
    
    def unfollow(self, user):
        """Unfollow a user (does not commit, caller should commit)"""
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            return True
        return False
    
    def accept_follow_request(self, follower):
        """Accept a pending follow request"""
        follow = self.followers.filter_by(follower_id=follower.id, status='pending').first()
        if follow:
            follow.status = 'accepted'
            return True
        return False
    
    def decline_follow_request(self, follower):
        """Decline a pending follow request"""
        follow = self.followers.filter_by(follower_id=follower.id, status='pending').first()
        if follow:
            db.session.delete(follow)
            return True
        return False
    
    def remove_follower(self, follower):
        """Remove a follower"""
        follow = self.followers.filter_by(follower_id=follower.id).first()
        if follow:
            db.session.delete(follow)
            return True
        return False
    
    def is_blocked(self, user):
        """Check if user is blocked by this user"""
        from app.models.blocked_users import BlockedUser
        return BlockedUser.query.filter_by(blocker_id=self.id, blocked_id=user.id).first() is not None
    
    def block_user(self, user):
        """Block a user (does not commit)"""
        if self.id == user.id:
            return False
        
        from app.models.blocked_users import BlockedUser
        # Remove any follow relationships
        self.unfollow(user)
        user.unfollow(self)
        
        # Check if already blocked
        if not self.is_blocked(user):
            blocked = BlockedUser(blocker_id=self.id, blocked_id=user.id)
            db.session.add(blocked)
            return True
        return False
    
    def unblock_user(self, user):
        """Unblock a user (does not commit)"""
        from app.models.blocked_users import BlockedUser
        blocked = BlockedUser.query.filter_by(blocker_id=self.id, blocked_id=user.id).first()
        if blocked:
            db.session.delete(blocked)
            return True
        return False
    
    def get_followers_count(self, viewer=None):
        """Get followers count - only accepted follows, exclude blocked"""
        from app.models.follows import Follow
        query = self.followers.filter_by(status='accepted')
        if viewer:
            from app.models.blocked_users import BlockedUser
            # Exclude users blocked by viewer
            blocked_ids = [b.blocked_id for b in BlockedUser.query.filter_by(blocker_id=viewer.id).all()]
            if blocked_ids:
                query = query.filter(~Follow.follower_id.in_(blocked_ids))
        return query.count()
    
    def get_following_count(self, viewer=None):
        """Get following count - only accepted follows, exclude blocked"""
        from app.models.follows import Follow
        query = self.following.filter_by(status='accepted')
        if viewer:
            from app.models.blocked_users import BlockedUser
            # Exclude users blocked by viewer
            blocked_ids = [b.blocked_id for b in BlockedUser.query.filter_by(blocker_id=viewer.id).all()]
            if blocked_ids:
                query = query.filter(~Follow.followed_id.in_(blocked_ids))
        return query.count()
    
    def __repr__(self):
        return f'<User {self.username}>'