from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Conversation, Message, ConversationMember
from extensions import db
from . import chat_bp
from .services import get_user_conversations, get_or_create_direct_conversation, save_media_file, save_message

@chat_bp.route('/home')
@chat_bp.route('/chat')
@login_required
def home():
    conversations = get_user_conversations(current_user.id)
    # Available approved users for new chats
    users = User.query.filter(User.id != current_user.id, User.status == 'approved').all()
    return render_template('home.html', conversations=conversations, users=users)

@chat_bp.route('/chat/<int:conversation_id>')
@login_required
def conversation_view(conversation_id):
    conv = Conversation.query.get_or_404(conversation_id)
    
    # Verify membership
    member = ConversationMember.query.filter_by(conversation_id=conv.id, user_id=current_user.id).first()
    if not member:
        flash('You are not a member of this chat.', 'danger')
        return redirect(url_for('chat.home'))

    # Determine recipient info for 1-on-1 chat
    recipient = None
    if not conv.is_group:
        other_m = ConversationMember.query.filter(
            ConversationMember.conversation_id == conv.id,
            ConversationMember.user_id != current_user.id
        ).first()
        if other_m:
            recipient = other_m.user

    messages = conv.messages.order_by(Message.id.asc()).all()
    return render_template('chat.html', conversation=conv, recipient=recipient, messages=messages)

@chat_bp.route('/chat/start/<int:target_user_id>')
@login_required
def start_chat(target_user_id):
    target = User.query.get_or_404(target_user_id)
    conv = get_or_create_direct_conversation(current_user.id, target.id)
    return redirect(url_for('chat.conversation_view', conversation_id=conv.id))

@chat_bp.route('/chat/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file attached'}), 400
        
        file = request.files['file']
        raw_conv_id = request.form.get('conversation_id')
        if not raw_conv_id:
            return jsonify({'status': 'error', 'message': 'Missing conversation ID'}), 400

        conversation_id = int(raw_conv_id)

        if file:
            relative_path = save_media_file(file)
            if relative_path:
                content_type = file.content_type or ''
                filename_lower = file.filename.lower() if file.filename else ''
                
                if content_type.startswith('image/'):
                    msg_type = 'image'
                elif content_type.startswith('audio/') or any(filename_lower.endswith(ext) for ext in ['.webm', '.wav', '.mp3', '.ogg', '.m4a']):
                    msg_type = 'audio'
                elif content_type.startswith('video/') or any(filename_lower.endswith(ext) for ext in ['.mp4', '.mov']):
                    msg_type = 'video'
                else:
                    msg_type = 'file'

                msg = save_message(
                    conversation_id=conversation_id,
                    sender_id=current_user.id,
                    content='',
                    message_type=msg_type,
                    file_path=relative_path
                )

                msg_dict = msg.to_dict()
                room = f"conversation_{conversation_id}"
                socketio.emit('new_message', msg_dict, room=room)

                return jsonify({'status': 'success', 'message': msg_dict})

        return jsonify({'status': 'error', 'message': 'Upload failed'}), 400
    except Exception as e:
        print(f"Upload handler exception: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
