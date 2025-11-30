"""
WebSocket event handlers for real-time messaging
"""
from flask import request
from datetime import datetime

from app.extension import socketio, db
from app.models.conversations import Conversation, ConversationParticipant
from app.models.messages import Message

# Store online users
online_users = set()
typing_users = {}  # {conversation_id: {user_id: timestamp}}

@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    # Flask-Login may not work directly with SocketIO, so we need to check session
    from flask import session
    from flask_login import login_user
    from app.models.users import User
    
    # Try to get user from session
    user_id = session.get('_user_id') or session.get('user_id')
    if not user_id:
        return False
    
    # Load user
    try:
        user = User.query.get(int(user_id))
        if not user or not user.is_active:
            return False
    except (ValueError, TypeError):
        return False
    
    # Add user to online users
    online_users.add(user.id)
    
    # Join user's personal room
    socketio.server.enter_room(request.sid, f"user_{user.id}")
    
    # Notify all conversations this user is in
    conversations = Conversation.query.join(ConversationParticipant).filter(
        ConversationParticipant.user_id == user.id
    ).all()
    
    for conv in conversations:
        socketio.server.enter_room(request.sid, f"conversation_{conv.id}")
        # Notify other participants
        other_user = conv.get_other_participant(user.id)
        if other_user:
            socketio.emit('user.online', {
                'user_id': user.id,
                'username': user.username,
                'online': True
            }, room=f"user_{other_user.id}")
    
    # Broadcast online status
    socketio.emit('user.online', {
        'user_id': user.id,
        'username': user.username,
        'online': True
    }, broadcast=True, include_self=False)
    
    return True


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import session
    from app.models.users import User
    
    user_id = session.get('_user_id') or session.get('user_id')
    if not user_id:
        return
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return
    except (ValueError, TypeError):
        return
    
    # Remove from online users
    online_users.discard(user.id)
    
    # Remove from typing users
    for conv_id in list(typing_users.keys()):
        if user.id in typing_users[conv_id]:
            del typing_users[conv_id][user.id]
            if not typing_users[conv_id]:
                del typing_users[conv_id]
    
    # Notify conversations
    conversations = Conversation.query.join(ConversationParticipant).filter(
        ConversationParticipant.user_id == user.id
    ).all()
    
    for conv in conversations:
        other_user = conv.get_other_participant(user.id)
        if other_user:
            socketio.emit('user.online', {
                'user_id': user.id,
                'username': user.username,
                'online': False
            }, room=f"user_{other_user.id}")
    
    # Broadcast offline status
    socketio.emit('user.online', {
        'user_id': user.id,
        'username': user.username,
        'online': False
    }, broadcast=True, include_self=False)


@socketio.on('typing.start')
def handle_typing_start(data):
    """Handle typing indicator start"""
    from flask import session
    from app.models.users import User
    
    user_id = session.get('_user_id') or session.get('user_id')
    if not user_id:
        return
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return
    except (ValueError, TypeError):
        return
    
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return
    
    # Verify user is a participant
    conv = Conversation.query.join(ConversationParticipant).filter(
        Conversation.id == conversation_id,
        ConversationParticipant.user_id == user.id
    ).first()
    
    if not conv:
        return
    
    # Add to typing users
    if conversation_id not in typing_users:
        typing_users[conversation_id] = {}
    typing_users[conversation_id][user.id] = datetime.utcnow()
    
    # Emit to other participants
    socketio.emit('user.typing', {
        'conversation_id': conversation_id,
        'user_id': user.id,
        'username': user.username,
        'typing': True
    }, room=f"conversation_{conversation_id}", skip_sid=request.sid)


@socketio.on('typing.stop')
def handle_typing_stop(data):
    """Handle typing indicator stop"""
    from flask import session
    from app.models.users import User
    
    user_id = session.get('_user_id') or session.get('user_id')
    if not user_id:
        return
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return
    except (ValueError, TypeError):
        return
    
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return
    
    # Remove from typing users
    if conversation_id in typing_users and user.id in typing_users[conversation_id]:
        del typing_users[conversation_id][user.id]
        if not typing_users[conversation_id]:
            del typing_users[conversation_id]
    
    # Emit to other participants
    socketio.emit('user.typing', {
        'conversation_id': conversation_id,
        'user_id': user.id,
        'username': user.username,
        'typing': False
    }, room=f"conversation_{conversation_id}", skip_sid=request.sid)


@socketio.on('message.read')
def handle_message_read(data):
    """Handle message read receipt"""
    from flask import session
    from app.models.users import User
    
    user_id = session.get('_user_id') or session.get('user_id')
    if not user_id:
        return
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return
    except (ValueError, TypeError):
        return
    
    message_id = data.get('message_id')
    conversation_id = data.get('conversation_id')
    
    if not message_id or not conversation_id:
        return
    
    # Verify user is a participant
    conv = Conversation.query.join(ConversationParticipant).filter(
        Conversation.id == conversation_id,
        ConversationParticipant.user_id == user.id
    ).first()
    
    if not conv:
        return
    
    # Mark message as read
    message = Message.query.filter_by(
        id=message_id,
        conversation_id=conversation_id
    ).first()
    
    if message and message.sender_id != user.id:
        message.mark_as_read()
        
        # Emit read receipt
        socketio.emit('message.read', {
            'message_id': message_id,
            'conversation_id': conversation_id,
            'user_id': user.id,
            'read_at': message.read_at.isoformat() if message.read_at else None
        }, room=f"conversation_{conversation_id}")


@socketio.on('join.conversation')
def handle_join_conversation(data):
    """Handle joining a conversation room"""
    from flask import session
    from app.models.users import User
    
    user_id = session.get('_user_id') or session.get('user_id')
    if not user_id:
        return False
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return False
    except (ValueError, TypeError):
        return False
    
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return False
    
    # Verify user is a participant
    conv = Conversation.query.join(ConversationParticipant).filter(
        Conversation.id == conversation_id,
        ConversationParticipant.user_id == user.id
    ).first()
    
    if conv:
        socketio.server.enter_room(request.sid, f"conversation_{conversation_id}")
        return True
    
    return False

