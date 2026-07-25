import uuid
from datetime import datetime, timedelta
from extensions import db
from models import User, AccountRequest, Invitation, Notification, Report
from blueprints.auth.utils import send_approval_email, send_rejection_email, send_friend_invite_email

def approve_request(request_id):
    req = AccountRequest.query.get(request_id)
    if not req or req.status != 'pending':
        return False, "Request not found or already processed."

    req.status = 'approved'
    
    # Create or update approved User
    user = User.query.filter_by(email=req.email).first()
    if not user:
        username = req.email.split('@')[0].capitalize()
        user = User(
            username=username,
            email=req.email,
            passcode=req.passcode or '1234',
            role='user',
            status='approved'
        )
        if req.password_hash:
            user.password_hash = req.password_hash
        else:
            user.set_password('OnlyUs123!')
        db.session.add(user)
    else:
        user.status = 'approved'
        if req.password_hash:
            user.password_hash = req.password_hash
        if req.passcode:
            user.passcode = req.passcode

    db.session.commit()

    # Send Approval Email Notification
    send_approval_email(req.email)
    if req.for_email and req.for_email != req.email:
        send_approval_email(req.for_email)

    return True, f"Approved request for {req.email}."

def reject_request(request_id):
    req = AccountRequest.query.get(request_id)
    if not req or req.status != 'pending':
        return False, "Request not found or already processed."

    req.status = 'rejected'
    db.session.commit()

    # Send Rejection Email Notification
    send_rejection_email(req.email)

    return True, f"Rejected request for {req.email}."

def report_request(request_id):
    req = AccountRequest.query.get(request_id)
    if not req:
        return False, "Request not found."

    req.status = 'reported'
    db.session.commit()
    return True, f"Reported request for {req.email}."

def approve_all_requests():
    pending_reqs = AccountRequest.query.filter_by(status='pending').all()
    count = 0
    for req in pending_reqs:
        approve_request(req.id)
        count += 1
    return count

def reject_all_requests():
    pending_reqs = AccountRequest.query.filter_by(status='pending').all()
    count = 0
    for req in pending_reqs:
        reject_request(req.id)
        count += 1
    return count

def generate_invitation(creator_id, recipient_email, passcode=None):
    code = str(uuid.uuid4())
    passcode = passcode or generate_4digit_passcode()
    inv = Invitation(
        code=code,
        passcode=passcode,
        created_by_id=creator_id,
        recipient_email=recipient_email,
        status='pending'
    )
    db.session.add(inv)
    
    # Also create pending AccountRequest
    creator = User.query.get(creator_id)
    sender_email = creator.email if creator else 'OnlyUs Admin'
    
    req = AccountRequest(
        email=recipient_email,
        from_email=sender_email,
        for_email=recipient_email,
        passcode=passcode,
        status='pending',
        note=f'Friend invitation from {sender_email}'
    )
    db.session.add(req)
    db.session.commit()

    # Send email notification to friend
    send_friend_invite_email(recipient_email, sender_email, passcode)
    return inv

def update_user_role(user_id, new_role):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    user.role = new_role
    db.session.commit()
    return True, f"Updated {user.username}'s role to {new_role}."
