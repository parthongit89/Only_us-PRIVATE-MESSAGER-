from flask import request
from flask_socketio import emit, join_room, leave_room
from extensions import socketio, db
from models import User
from .services import save_message

@socketio.on('connect')
def handle_connect():
    print(f"Socket connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Socket disconnected: {request.sid}")

@socketio.on('join_conversation')
def handle_join_conversation(data):
    room = f"conversation_{data.get('conversation_id')}"
    join_room(room)
    emit('status', {'msg': f'User joined room {room}'}, room=room)

@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    room = f"conversation_{data.get('conversation_id')}"
    leave_room(room)

@socketio.on('send_message')
def handle_send_message(data):
    conversation_id = data.get('conversation_id')
    sender_id = data.get('sender_id')
    content = data.get('content')
    message_type = data.get('message_type', 'text')
    file_path = data.get('file_path')

    if conversation_id and sender_id and (content or file_path):
        msg = save_message(conversation_id, sender_id, content, message_type, file_path)
        room = f"conversation_{conversation_id}"
        emit('new_message', msg.to_dict(), room=room)

@socketio.on('typing')
def handle_typing(data):
    conversation_id = data.get('conversation_id')
    user_name = data.get('user_name')
    is_typing = data.get('is_typing', False)
    room = f"conversation_{conversation_id}"
    emit('typing_status', {'user_name': user_name, 'is_typing': is_typing}, room=room, include_self=False)
