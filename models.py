from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager

IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.now(IST).replace(tzinfo=None)

@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        return None
    uid = str(user_id).strip()
    return User.query.filter(User.id == uid).first()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(32), primary_key=True) # Custom ID e.g. ON0001, ON0002
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    passcode = db.Column(db.String(10), nullable=True) # 4-digit passcode
    role = db.Column(db.String(20), default='user', nullable=False)  # owner, admin, user
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
    avatar = db.Column(db.String(255), default='default_avatar.png')
    bio = db.Column(db.String(255), default='Hey there! I am using OnlyUs.')
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=get_ist_now)
    created_at = db.Column(db.DateTime, default=get_ist_now)

    # Relationships
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    @property
    def id_hash(self):
        from blueprints.auth.security import hash_text
        return hash_text(str(self.id))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_passcode(self, passcode):
        from blueprints.auth.security import hash_passcode
        self.passcode = hash_passcode(passcode)

    def check_passcode(self, passcode):
        from blueprints.auth.security import check_passcode_hash
        return check_passcode_hash(self.passcode, passcode)

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_admin_or_owner(self):
        return self.role in ['owner', 'admin']

    def to_dict(self):
        return {
            'id': self.id,
            'id_hash': self.id_hash,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'avatar': self.avatar,
            'bio': self.bio,
            'is_online': self.is_online,
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M:%S') if self.last_seen else None
        }

class AccountRequest(db.Model):
    __tablename__ = 'account_requests'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    passcode = db.Column(db.String(10), nullable=True) # 4-digit passcode
    from_email = db.Column(db.String(120), nullable=True)
    for_email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected, reported
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'from_email': self.from_email,
            'for_email': self.for_email,
            'passcode': self.passcode,
            'status': self.status,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Invitation(db.Model):
    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    passcode = db.Column(db.String(10), nullable=True) # 4-digit passcode
    created_by_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, expired
    created_at = db.Column(db.DateTime, default=get_ist_now)
    expires_at = db.Column(db.DateTime, default=lambda: get_ist_now() + timedelta(days=7))

    creator = db.relationship('User', foreign_keys=[created_by_id])

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    is_group = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(255), default='group_avatar.png')
    created_at = db.Column(db.DateTime, default=get_ist_now)

    members = db.relationship('ConversationMember', backref='conversation', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='conversation', cascade='all, delete-orphan', lazy='dynamic')

class ConversationMember(db.Model):
    __tablename__ = 'conversation_members'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(20), default='member')  # member, admin
    joined_at = db.Column(db.DateTime, default=get_ist_now)

    user = db.relationship('User')

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    sender_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, audio
    file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='sent')  # sent, delivered, read
    created_at = db.Column(db.DateTime, default=get_ist_now)

    @property
    def decrypted_content(self):
        from blueprints.auth.security import decrypt_message_content
        return decrypt_message_content(self.content)

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username if self.sender else 'Unknown',
            'sender_avatar': self.sender.avatar if self.sender else 'default_avatar.png',
            'content': self.decrypted_content,
            'message_type': self.message_type,
            'file_path': self.file_path,
            'status': self.status,
            'created_at': self.created_at.strftime('%I:%M %p') if self.created_at else ''
        }

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=True, default='') # Legacy compatibility column
    message_hash = db.Column(db.String(256), nullable=True) # Nullable for migration compatibility
    type = db.Column(db.String(30), default='system')  # system, request, invite, chat
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_ist_now)


    @property
    def display_hash(self):
        if self.message_hash:
            return str(self.message_hash)[:24]
        return "e3b0c44298fc1c149afbf4c8"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message_hash': self.display_hash,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%d %b, %I:%M %p') if self.created_at else ''
        }


class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'

    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False, index=True)
    blocked_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=get_ist_now)


    blocker = db.relationship('User', foreign_keys=[blocker_id])
    blocked = db.relationship('User', foreign_keys=[blocked_id])

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False)
    reported_user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, dismissed
    created_at = db.Column(db.DateTime, default=get_ist_now)

    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])

