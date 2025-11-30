from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
import os

from app.extension import db
from app.models.conversations import Conversation, ConversationParticipant
from app.models.messages import Message, MessageReaction
from app.models.users import User
from app.models.notifications import Notification
from app.utils import allowed_file

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")

@messages_bp.route("/")
@login_required
def list_conversations():
    """List all conversations for the current user"""
    # Get all conversations where current user is a participant
    conversations = db.session.query(Conversation).join(
        ConversationParticipant
    ).filter(
        ConversationParticipant.user_id == current_user.id
    ).options(
        joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
    ).order_by(Conversation.updated_at.desc()).all()
    
    # Format conversations with last message and unread count
    conversations_data = []
    for conv in conversations:
        other_user = conv.get_other_participant(current_user.id)
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(current_user.id)
        
        conversations_data.append({
            'id': conv.id,
            'other_user': {
                'id': other_user.id if other_user else None,
                'username': other_user.username if other_user else 'Unknown',
                'profile_picture': other_user.profile_picture if other_user else None,
                'is_verified': other_user.is_verified if other_user else False
            },
            'last_message': {
                'content': last_message.content if last_message else None,
                'type': last_message.message_type if last_message else None,
                'created_at': last_message.created_at.isoformat() if last_message else None,
                'sender_id': last_message.sender_id if last_message else None
            } if last_message else None,
            'unread_count': unread_count,
            'updated_at': conv.updated_at.isoformat()
        })
    
    return render_template("messages/list.html", conversations=conversations_data)


@messages_bp.route("/<int:conversation_id>")
@login_required
def view_conversation(conversation_id):
    """View a specific conversation thread"""
    # Verify user is a participant
    conv = Conversation.query.join(ConversationParticipant).filter(
        Conversation.id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    ).first_or_404()
    
    # Get other participant
    other_user = conv.get_other_participant(current_user.id)
    
    # Get messages
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .options(joinedload(Message.sender))\
        .options(joinedload(Message.reply_to))\
        .order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    conv.mark_as_read(current_user.id)
    
    # Format messages
    messages_data = []
    for msg in messages:
        reactions_data = []
        for reaction in msg.reactions:
            reactions_data.append({
                'id': reaction.id,
                'emoji': reaction.emoji,
                'user_id': reaction.user_id,
                'username': reaction.user.username
            })
        
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'type': msg.message_type,
            'media_url': msg.media_url,
            'reply_to': {
                'id': msg.reply_to.id,
                'content': msg.reply_to.content[:50] if msg.reply_to else None,
                'sender_username': msg.reply_to.sender.username if msg.reply_to else None
            } if msg.reply_to else None,
            'reactions': reactions_data,
            'read': msg.read,
            'read_at': msg.read_at.isoformat() if msg.read_at else None,
            'created_at': msg.created_at.isoformat(),
            'sender': {
                'id': msg.sender.id,
                'username': msg.sender.username,
                'profile_picture': msg.sender.profile_picture
            }
        })
    
    return render_template("messages/thread.html", 
                         conversation=conv, 
                         other_user=other_user,
                         messages=messages_data)


@messages_bp.route("/api/conversations", methods=["GET"])
@login_required
def api_list_conversations():
    """API endpoint to list conversations"""
    conversations = db.session.query(Conversation).join(
        ConversationParticipant
    ).filter(
        ConversationParticipant.user_id == current_user.id
    ).options(
        joinedload(Conversation.participants).joinedload(ConversationParticipant.user)
    ).order_by(Conversation.updated_at.desc()).all()
    
    conversations_data = []
    for conv in conversations:
        other_user = conv.get_other_participant(current_user.id)
        last_message = conv.get_last_message()
        unread_count = conv.get_unread_count(current_user.id)
        
        conversations_data.append({
            'id': conv.id,
            'other_user': {
                'id': other_user.id if other_user else None,
                'username': other_user.username if other_user else 'Unknown',
                'profile_picture': other_user.profile_picture if other_user else None,
                'is_verified': other_user.is_verified if other_user else False
            },
            'last_message': {
                'content': last_message.content if last_message else None,
                'type': last_message.message_type if last_message else None,
                'created_at': last_message.created_at.isoformat() if last_message else None,
                'sender_id': last_message.sender_id if last_message else None
            } if last_message else None,
            'unread_count': unread_count,
            'updated_at': conv.updated_at.isoformat()
        })
    
    return jsonify(conversations_data)


@messages_bp.route("/api/conversations/<int:conversation_id>/messages", methods=["GET"])
@login_required
def api_get_messages(conversation_id):
    """API endpoint to get messages in a conversation"""
    # Verify user is a participant
    conv = Conversation.query.join(ConversationParticipant).filter(
        Conversation.id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    ).first_or_404()
    
    # Get messages
    messages = Message.query.filter_by(conversation_id=conversation_id)\
        .options(joinedload(Message.sender))\
        .options(joinedload(Message.reply_to))\
        .order_by(Message.created_at.asc()).all()
    
    # Mark as read
    conv.mark_as_read(current_user.id)
    
    messages_data = []
    for msg in messages:
        reactions_data = []
        for reaction in msg.reactions:
            reactions_data.append({
                'id': reaction.id,
                'emoji': reaction.emoji,
                'user_id': reaction.user_id,
                'username': reaction.user.username
            })
        
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'type': msg.message_type,
            'media_url': msg.media_url,
            'reply_to': {
                'id': msg.reply_to.id,
                'content': msg.reply_to.content[:50] if msg.reply_to else None,
                'sender_username': msg.reply_to.sender.username if msg.reply_to else None
            } if msg.reply_to else None,
            'reactions': reactions_data,
            'read': msg.read,
            'read_at': msg.read_at.isoformat() if msg.read_at else None,
            'created_at': msg.created_at.isoformat(),
            'sender': {
                'id': msg.sender.id,
                'username': msg.sender.username,
                'profile_picture': msg.sender.profile_picture
            }
        })
    
    return jsonify(messages_data)


@messages_bp.route("/api/conversations/<int:conversation_id>/messages", methods=["POST"])
@login_required
def api_send_message(conversation_id):
    """API endpoint to send a message"""
    # Handle both JSON and FormData
    if request.is_json:
        data = request.get_json()
        content = data.get('content')
        message_type = data.get('type', 'text')
        media_url = data.get('media_url')
        reply_to_id = data.get('reply_to_id')
    else:
        content = request.form.get('content')
        message_type = request.form.get('type', 'text')
        media_url = request.form.get('media_url')
        reply_to_id = request.form.get('reply_to_id')
    
    if not content and not (request.files and 'file' in request.files):
        return jsonify({'error': 'Content or media is required'}), 400
    
    # Verify user is a participant or create conversation
    if conversation_id == 0:
        # New conversation - need recipient_id
        if request.is_json:
            recipient_id = data.get('recipient_id')
        else:
            recipient_id = request.form.get('recipient_id')
        
        if not recipient_id:
            return jsonify({'error': 'recipient_id required for new conversation'}), 400
        
        recipient = User.query.get_or_404(recipient_id)
        conv = Conversation.get_or_create_conversation(current_user.id, int(recipient_id))
    else:
        conv = Conversation.query.join(ConversationParticipant).filter(
            Conversation.id == conversation_id,
            ConversationParticipant.user_id == current_user.id
        ).first_or_404()
    
    # Verify reply_to message belongs to this conversation
    reply_to = None
    if reply_to_id:
        try:
            reply_to_id = int(reply_to_id)
            reply_to = Message.query.filter_by(
                id=reply_to_id,
                conversation_id=conv.id
            ).first()
            if not reply_to:
                return jsonify({'error': 'Invalid reply_to message'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid reply_to_id'}), 400
    
    # Handle file upload if present
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            from flask import current_app
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'messages')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save file with secure filename
            from werkzeug.utils import secure_filename
            timestamp = int(datetime.utcnow().timestamp())
            original_filename = secure_filename(file.filename)
            filename = f"{current_user.id}_{timestamp}_{original_filename}"
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            media_url = f"/uploads/messages/{filename}"
            
            # Determine message type from file extension
            if file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                message_type = 'video'
            elif file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                message_type = 'voice'
            else:
                message_type = 'image'
    
    # Create message
    message = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        content=content,
        message_type=message_type,
        media_url=media_url,
        reply_to_id=reply_to_id
    )
    
    # Update conversation timestamp
    conv.updated_at = datetime.utcnow()
    
    db.session.add(message)
    
    # Create notification for recipient
    other_user = conv.get_other_participant(current_user.id)
    if other_user:
        notification = Notification(
            user_id=other_user.id,
            from_user_id=current_user.id,
            notification_type='message',
            conversation_id=conv.id,
            message_id=message.id
        )
        db.session.add(notification)
    
    db.session.commit()
    
    # Emit WebSocket event (will be handled by socketio handlers)
    from app.extension import socketio
    socketio.emit('message.new', {
        'message': {
            'id': message.id,
            'conversation_id': conv.id,
            'sender_id': current_user.id,
            'content': content,
            'type': message_type,
            'media_url': media_url,
            'reply_to_id': reply_to_id,
            'created_at': message.created_at.isoformat(),
            'sender': {
                'username': current_user.username,
                'profile_picture': current_user.profile_picture
            }
        }
    }, room=f"conversation_{conv.id}")
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'conversation_id': conv.id,
            'sender_id': current_user.id,
            'content': content,
            'type': message_type,
            'media_url': media_url,
            'reply_to_id': reply_to_id,
            'created_at': message.created_at.isoformat()
        }
    }), 201


@messages_bp.route("/api/messages/<int:message_id>", methods=["DELETE"])
@login_required
def api_delete_message(message_id):
    """API endpoint to delete a message"""
    message = Message.query.get_or_404(message_id)
    
    # Only sender can delete
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    conversation_id = message.conversation_id
    db.session.delete(message)
    db.session.commit()
    
    # Emit WebSocket event
    from app.extension import socketio
    socketio.emit('message.deleted', {
        'message_id': message_id,
        'conversation_id': conversation_id
    }, room=f"conversation_{conversation_id}")
    
    return jsonify({'success': True})


@messages_bp.route("/api/messages/<int:message_id>/react", methods=["POST"])
@login_required
def api_react_to_message(message_id):
    """API endpoint to react to a message"""
    message = Message.query.get_or_404(message_id)
    data = request.get_json()
    emoji = data.get('emoji')
    
    if not emoji:
        return jsonify({'error': 'Emoji is required'}), 400
    
    # Check if user already reacted with this emoji
    existing_reaction = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=current_user.id,
        emoji=emoji
    ).first()
    
    if existing_reaction:
        # Remove reaction
        db.session.delete(existing_reaction)
        action = 'removed'
    else:
        # Add reaction
        reaction = MessageReaction(
            message_id=message_id,
            user_id=current_user.id,
            emoji=emoji
        )
        db.session.add(reaction)
        action = 'added'
    
    db.session.commit()
    
    # Emit WebSocket event
    from app.extension import socketio
    socketio.emit('message.reaction', {
        'message_id': message_id,
        'conversation_id': message.conversation_id,
        'user_id': current_user.id,
        'username': current_user.username,
        'emoji': emoji,
        'action': action
    }, room=f"conversation_{message.conversation_id}")
    
    return jsonify({
        'success': True,
        'action': action,
        'emoji': emoji
    })


@messages_bp.route("/api/start/<int:user_id>", methods=["POST"])
@login_required
def api_start_conversation(user_id):
    """API endpoint to start a new conversation with a user"""
    recipient = User.query.get_or_404(user_id)
    
    if recipient.id == current_user.id:
        return jsonify({'error': 'Cannot start conversation with yourself'}), 400
    
    # Get or create conversation
    conv = Conversation.get_or_create_conversation(current_user.id, user_id)
    
    return jsonify({
        'success': True,
        'conversation_id': conv.id
    })

