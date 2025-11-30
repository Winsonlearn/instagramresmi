from app.extension import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = "messages"
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)  # Nullable for media-only messages
    message_type = db.Column(db.String(20), default='text', nullable=False)  # 'text', 'image', 'video', 'voice'
    media_url = db.Column(db.String(255), nullable=True)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    sender = db.relationship('User', backref='sent_messages')
    reply_to = db.relationship('Message', remote_side=[id], backref='replies')
    reactions = db.relationship(
        'MessageReaction',
        backref='message',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.read:
            self.read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def get_reaction_count(self, emoji=None):
        """Get count of reactions, optionally filtered by emoji"""
        if emoji:
            return self.reactions.filter_by(emoji=emoji).count()
        return self.reactions.count()
    
    def has_user_reacted(self, user_id, emoji=None):
        """Check if user has reacted, optionally with specific emoji"""
        query = self.reactions.filter_by(user_id=user_id)
        if emoji:
            query = query.filter_by(emoji=emoji)
        return query.first() is not None
    
    def __repr__(self):
        return f'<Message {self.id} in Conversation {self.conversation_id}>'


class MessageReaction(db.Model):
    __tablename__ = "message_reactions"
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    emoji = db.Column(db.String(10), nullable=False)  # Store emoji as string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='message_reactions')
    
    # Ensure unique combination (one reaction per user per message per emoji)
    __table_args__ = (db.UniqueConstraint('message_id', 'user_id', 'emoji', name='_message_user_emoji_uc'),)
    
    def __repr__(self):
        return f'<MessageReaction {self.emoji} on Message {self.message_id} by User {self.user_id}>'


