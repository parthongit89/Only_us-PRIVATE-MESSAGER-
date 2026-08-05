import os
from datetime import datetime
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Conversation, ConversationMember, Message, Notification
from config import Config

from blueprints.auth.security import encrypt_message_content, decrypt_message_content, validate_upload_file, hash_text

def get_or_create_direct_conversation(user1_id, user2_id):
    u1_str = str(user1_id).strip()
    u2_str = str(user2_id).strip()
    
    # Find existing direct conversation between user1 and user2
    user1_convs = db.session.query(ConversationMember.conversation_id)\
        .filter(ConversationMember.user_id == u1_str).all()
    user1_conv_ids = [c[0] for c in user1_convs]

    existing = db.session.query(Conversation)\
        .join(ConversationMember)\
        .filter(Conversation.is_group == False)\
        .filter(Conversation.id.in_(user1_conv_ids))\
        .filter(ConversationMember.user_id == u2_str).first()

    if existing:
        return existing

    # Create new 1-on-1 conversation
    conv = Conversation(is_group=False)
    db.session.add(conv)
    db.session.commit()

    cm1 = ConversationMember(conversation_id=conv.id, user_id=u1_str)
    cm2 = ConversationMember(conversation_id=conv.id, user_id=u2_str)
    db.session.add_all([cm1, cm2])
    db.session.commit()

    return conv

def get_user_conversations(user_id):
    uid_str = str(user_id).strip()
    memberships = ConversationMember.query.filter_by(user_id=uid_str).all()
    conv_list = []
    
    for m in memberships:
        conv = m.conversation
        if not conv.is_group:
            other_member = ConversationMember.query.filter(
                ConversationMember.conversation_id == conv.id,
                ConversationMember.user_id != uid_str
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
        decrypted_last_msg = decrypt_message_content(last_msg.content) if (last_msg and last_msg.content) else ""
        
        conv_list.append({
            'id': conv.id,
            'name': name,
            'avatar': avatar,
            'is_online': is_online,
            'is_group': conv.is_group,
            'last_message': (decrypted_last_msg if last_msg.message_type == 'text' else f"[{last_msg.message_type.capitalize()}]") if last_msg else "No messages yet",
            'last_message_time': last_msg.created_at.strftime('%I:%M %p') if (last_msg and last_msg.created_at) else ""
        })
    return conv_list

def save_message(conversation_id, sender_id, content, message_type='text', file_path=None):
    sender_id_str = str(sender_id).strip()
    encrypted_content = encrypt_message_content(content) if content else ""
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id_str,
        content=encrypted_content,
        message_type=message_type,
        file_path=file_path,
        status='sent'
    )
    db.session.add(msg)

    # Create in-app Notification for recipients safely
    try:
        sender = User.query.filter(User.id == sender_id_str).first()
        sender_name = sender.username if sender else "Someone"
        preview = content if message_type == 'text' else f"[{message_type.capitalize()}]"

        other_members = ConversationMember.query.filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id != sender_id_str
        ).all()

        for m in other_members:
            notif = Notification(
                user_id=str(m.user_id),
                title=f"New message from {sender_name}",
                message_hash=hash_text(preview),
                type="message"
            )
            db.session.add(notif)
    except Exception as notif_err:
        print(f"[SAVE MESSAGE NOTIF WARNING] {notif_err}")

    db.session.commit()
    return msg



def save_media_file(file):
    if not file:
        return None
    valid, err_msg = validate_upload_file(file)
    if not valid:
        raise ValueError(err_msg)

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    content_type = (file.content_type or '').lower()
    
    raw_name = file.filename or ''
    if not raw_name or raw_name.lower() in ['blob', 'file', 'attachment']:
        if content_type.startswith('image/'):
            sub_ext = content_type.split('/')[-1] if '/' in content_type else 'jpg'
            if sub_ext == 'jpeg': sub_ext = 'jpg'
            raw_name = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{sub_ext}"
        elif content_type.startswith('audio/'):
            sub_ext = 'webm'
            if 'mp4' in content_type or 'm4a' in content_type: sub_ext = 'm4a'
            elif 'mpeg' in content_type or 'mp3' in content_type: sub_ext = 'mp3'
            elif 'wav' in content_type: sub_ext = 'wav'
            raw_name = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{sub_ext}"
        elif content_type.startswith('video/'):
            raw_name = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        else:
            raw_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"

    filename = secure_filename(raw_name)
    if not filename or '.' not in filename:
        if content_type.startswith('image/'):
            filename = (filename or 'image') + '.jpg'
        elif content_type.startswith('audio/'):
            filename = (filename or 'voice') + '.webm'
        elif content_type.startswith('video/'):
            filename = (filename or 'video') + '.mp4'

    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(filepath)
    return f"uploads/{unique_filename}"

