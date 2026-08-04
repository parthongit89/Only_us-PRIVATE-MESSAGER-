from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from flask import session
from extensions import db
from models import User, AccountRequest, Notification, get_ist_now
from .security import hash_text
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

    db.session.commit()

    # Send notification to admins with hashed message summary
    try:
        admins = User.query.filter(User.role.in_(['admin', 'owner'])).all()
        msg_summary = f"Account request from {email}."
        for admin in admins:
            notif = Notification(
                user_id=str(admin.id),
                title='New Account Request',
                message_hash=hash_text(msg_summary),
                type='request'
            )
            db.session.add(notif)
        db.session.commit()
    except Exception as notif_err:
        print(f"[ACCOUNT REQUEST NOTIF WARNING] {notif_err}")
        db.session.rollback()


    # Send Email Notification to requesting user or friend
    if from_email and for_email and from_email != for_email:
        send_friend_invite_email(for_email, from_email, passcode)
    else:
        send_request_received_email(email)

    return req, True

def generate_and_send_otp(email):
    code = generate_otp(6)
    now = get_ist_now()
    expires_ts = (now + timedelta(minutes=10)).timestamp()
    
    # Save hashed OTP & expiration in session (No database table persistence needed)
    session['otp_hash'] = hash_text(str(code))
    session['otp_expires'] = expires_ts

    send_otp_email(email, code)
    return code

def verify_otp_code(email, code):
    now_ts = get_ist_now().timestamp()
    stored_hash = session.get('otp_hash')
    expires_ts = session.get('otp_expires', 0)

    if stored_hash and expires_ts and now_ts < expires_ts:
        if hash_text(str(code)) == stored_hash:
            session.pop('otp_hash', None)
            session.pop('otp_expires', None)
            return True
    return False


