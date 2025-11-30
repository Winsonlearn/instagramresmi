from app.extension import db
from datetime import datetime
from sqlalchemy import func

class Conversation(db.Model):
    __tablename__ = "conversations"
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    # Relationships
    participants = db.relationship(
        'ConversationParticipant',
        backref='conversation',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    messages = db.relationship(
        'Message',
        backref='conversation',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Message.created_at'
    )
    
    def get_other_participant(self, user_id):
        """Get the other participant in a 1-on-1 conversation"""
        for participant in self.participants:
            if participant.user_id != user_id:
                return participant.user
        return None
    
    def get_last_message(self):
        """Get the most recent message"""
        from app.models.messages import Message
        return Message.query.filter_by(conversation_id=self.id).order_by(Message.created_at.desc()).first()
    
    def get_unread_count(self, user_id):
        """Get count of unread messages for a user"""
        from app.models.messages import Message
        return Message.query.filter_by(
            conversation_id=self.id,
            read=False
        ).filter(Message.sender_id != user_id).count()
    
    def mark_as_read(self, user_id):
        """Mark all messages as read for a user"""
        from app.models.messages import Message
        Message.query.filter_by(
            conversation_id=self.id,
            read=False
        ).filter(Message.sender_id != user_id).update({Message.read: True}, synchronize_session=False)
        db.session.commit()
    
    @staticmethod
    def get_or_create_conversation(user1_id, user2_id):
        """Get existing conversation between two users or create a new one"""
        # Check if conversation already exists between these two users
        # Find conversations with exactly these two participants
        
        # Get all conversations with user1
        user1_convs = db.session.query(ConversationParticipant.conversation_id)\
            .filter(ConversationParticipant.user_id == user1_id).subquery()
        
        # Get conversations with user2 that also have user1
        existing_conv = db.session.query(ConversationParticipant.conversation_id)\
            .filter(ConversationParticipant.user_id == user2_id)\
            .filter(ConversationParticipant.conversation_id.in_(db.session.query(user1_convs.c.conversation_id)))\
            .first()
        
        if existing_conv:
            return Conversation.query.get(existing_conv[0])
        
        # Create new conversation
        conv = Conversation()
        db.session.add(conv)
        db.session.flush()
        
        # Add participants
        participant1 = ConversationParticipant(conversation_id=conv.id, user_id=user1_id)
        participant2 = ConversationParticipant(conversation_id=conv.id, user_id=user2_id)
        db.session.add(participant1)
        db.session.add(participant2)
        db.session.commit()
        
        return conv
    
    def __repr__(self):
        return f'<Conversation {self.id}>'


class ConversationParticipant(db.Model):
    __tablename__ = "conversation_participants"
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='conversations')
    
    # Ensure unique combination
    __table_args__ = (db.UniqueConstraint('conversation_id', 'user_id', name='_conversation_user_uc'),)
    
    def __repr__(self):
        return f'<ConversationParticipant {self.conversation_id} - User {self.user_id}>'

