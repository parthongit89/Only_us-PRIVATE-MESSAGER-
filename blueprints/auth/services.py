from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, AccountRequest, OTPCode, Notification
from .utils import (
    generate_otp, generate_4digit_passcode, send_otp_email,
    send_request_received_email, send_friend_invite_email
)

def create_access_request(email, password=None, passcode=None, from_email=None, for_email=None):
    # Hash password if provided
    password_hash = generate_password_hash(password) if password else None
    
    # Auto-generate 4-digit passcode if not provided
    if not passcode or len(str(passcode).strip()) != 4:
        passcode = generate_4digit_passcode()

    req = AccountRequest.query.filter_by(email=email, status='pending').first()
    if not req:
        req = AccountRequest(
            email=email,
            password_hash=password_hash,
            passcode=passcode,
            from_email=from_email or email,
            for_email=for_email or email,
            status='pending',
            note='Request application for creating Account'
        )
        db.session.add(req)
    else:
        if password_hash:
            req.password_hash = password_hash
        req.passcode = passcode

    # Send notification to admins
    admins = User.query.filter(User.role.in_(['admin', 'owner'])).all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            title='New Account Request',
            message=f'{email} requested access to OnlyUs with passcode {passcode}.',
            type='request'
        )
        db.session.add(notif)

    db.session.commit()

    # Send Email Notification to requesting user or friend
    if from_email and for_email and from_email != for_email:
        send_friend_invite_email(for_email, from_email, passcode)
    else:
        send_request_received_email(email)

    return req, True

def generate_and_send_otp(email):
    code = generate_otp(6)
    expires = datetime.utcnow() + timedelta(minutes=10)
    
    otp_record = OTPCode(email=email, code=code, expires_at=expires)
    db.session.add(otp_record)
    db.session.commit()

    send_otp_email(email, code)
    return code

def verify_otp_code(email, code):
    record = OTPCode.query.filter_by(email=email, code=code, is_used=False)\
                          .filter(OTPCode.expires_at > datetime.utcnow())\
                          .order_by(OTPCode.id.desc()).first()
    if record:
        record.is_used = True
        db.session.commit()
        return True
    return False
