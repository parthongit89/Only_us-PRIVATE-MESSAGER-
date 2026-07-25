import os
from datetime import datetime
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Conversation, ConversationMember, Message
from config import Config

def get_or_create_direct_conversation(user1_id, user2_id):
    # Find existing direct conversation between user1 and user2
    user1_convs = db.session.query(ConversationMember.conversation_id)\
        .filter(ConversationMember.user_id == user1_id).all()
    user1_conv_ids = [c[0] for c in user1_convs]

    existing = db.session.query(Conversation)\
        .join(ConversationMember)\
        .filter(Conversation.is_group == False)\
        .filter(Conversation.id.in_(user1_conv_ids))\
        .filter(ConversationMember.user_id == user2_id).first()

    if existing:
        return existing

    # Create new 1-on-1 conversation
    conv = Conversation(is_group=False)
    db.session.add(conv)
    db.session.commit()

    cm1 = ConversationMember(conversation_id=conv.id, user_id=user1_id)
    cm2 = ConversationMember(conversation_id=conv.id, user_id=user2_id)
    db.session.add_all([cm1, cm2])
    db.session.commit()

    return conv

def get_user_conversations(user_id):
    memberships = ConversationMember.query.filter_by(user_id=user_id).all()
    conv_list = []
    
    for m in memberships:
        conv = m.conversation
        if not conv.is_group:
            other_member = ConversationMember.query.filter(
                ConversationMember.conversation_id == conv.id,
                ConversationMember.user_id != user_id
            ).first()
            other_user = other_member.user if other_member else None
            name = other_user.username if other_user else "Chat"
            avatar = other_user.avatar if other_user else "default_avatar.png"
            is_online = other_user.is_online if other_user else False
        else:
            name = conv.name or "Group Chat"
            avatar = conv.avatar or "group_avatar.png"
            is_online = False

        last_msg = conv.messages.order_by(Message.id.desc()).first()
        
        conv_list.append({
            'id': conv.id,
            'name': name,
            'avatar': avatar,
            'is_online': is_online,
            'is_group': conv.is_group,
            'last_message': (last_msg.content if last_msg.message_type == 'text' else f"[{last_msg.message_type.capitalize()}]") if last_msg else "No messages yet",
            'last_message_time': last_msg.created_at.strftime('%I:%M %p') if (last_msg and last_msg.created_at) else ""
        })
    return conv_list

def save_message(conversation_id, sender_id, content, message_type='text', file_path=None):
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
        file_path=file_path,
        status='sent'
    )
    db.session.add(msg)
    db.session.commit()
    return msg

def save_media_file(file):
    if not file:
        return None
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    raw_name = file.filename or 'voice_note.webm'
    if raw_name in ['blob', '', None]:
        raw_name = 'voice_note.webm'
    filename = secure_filename(raw_name)
    if not filename:
        filename = 'voice_note.webm'
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(filepath)
    return f"uploads/{unique_filename}"
