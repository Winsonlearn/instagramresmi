from app.extension import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
import json

class Post(db.Model):
    __tablename__ = "posts"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    # Support for carousel: store as JSON array of media objects
    # Each media object: {"url": "...", "type": "image|video", "alt_text": "..."}
    media_urls = db.Column(db.Text, nullable=True)  # JSON string (nullable for backward compatibility)
    # Legacy column for old posts (mapped to database column 'image_url')
    # Use server_default to avoid NOT NULL constraint issues
    _image_url_db = db.Column('image_url', db.String(255), nullable=True, server_default='')
    caption = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_media_list(self):
        """Get list of media objects"""
        # Try media_urls first
        if self.media_urls:
            try:
                return json.loads(self.media_urls) if self.media_urls else []
            except (json.JSONDecodeError, TypeError):
                # Backward compatibility: if old format (single URL string)
                if isinstance(self.media_urls, str) and not self.media_urls.startswith('['):
                    return [{"url": self.media_urls, "type": "image", "alt_text": ""}]
        
        # Fallback to legacy image_url column if media_urls is empty
        if self._image_url_db:
            return [{"url": self._image_url_db, "type": "image", "alt_text": ""}]
        
        return []
    
    # Backward compatibility: get first media URL using hybrid_property
    @hybrid_property
    def image_url(self):
        """Get first media URL for backward compatibility"""
        media_list = self.get_media_list()
        if media_list and len(media_list) > 0:
            return media_list[0]['url']
        # Fallback to legacy _image_url_db column if exists
        return self._image_url_db if self._image_url_db else None
    
    def set_media_list(self, media_list):
        """Set media list"""
        self.media_urls = json.dumps(media_list)
    
    def extract_hashtags(self):
        """Extract hashtags from caption"""
        if not self.caption:
            return []
        import re
        hashtags = re.findall(r'#(\w+)', self.caption)
        return list(set(hashtags))  # Return unique hashtags
    
    def extract_mentions(self):
        """Extract user mentions from caption"""
        if not self.caption:
            return []
        import re
        mentions = re.findall(r'@(\w+)', self.caption)
        return list(set(mentions))  # Return unique mentions
    
    def is_liked_by(self, user):
        """Check if post is liked by user"""
        if user is None or not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None
    
    def like_count(self):
        """Get total number of likes"""
        return self.likes.count()
    
    def comment_count(self):
        """Get total number of comments"""
        return self.comments.count()
    
    def is_bookmarked_by(self, user):
        """Check if post is bookmarked by user"""
        if user is None or not user.is_authenticated:
            return False
        return self.bookmarks.filter_by(user_id=user.id).first() is not None
    
    def __repr__(self):
        return f'<Post {self.id} by User {self.user_id}>'

