import uuid
from datetime import datetime, timedelta
from extensions import db
from models import User, AccountRequest, Invitation, Notification, Report
from blueprints.auth.utils import send_approval_email, send_rejection_email, send_friend_invite_email, generate_4digit_passcode

def approve_request(request_id):
    req = AccountRequest.query.get(request_id)
    if not req or req.status != 'pending':
        return False, "Request not found or already processed."

    req.status = 'approved'
    
    # Create or update approved User
    user = User.query.filter_by(email=req.email).first()
    if not user:
        from blueprints.auth.security import generate_next_custom_user_id, hash_text
        username = req.email.split('@')[0].capitalize()
        new_id = generate_next_custom_user_id()
        user = User(
            id=new_id,
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

    # Automatically initiate direct conversation column between Inviter and Invited user
    if req.from_email and req.from_email != req.email:
        inviter = User.query.filter_by(email=req.from_email).first()
        if inviter and inviter.id != user.id:
            from blueprints.auth.security import hash_text
            from blueprints.chat.services import get_or_create_direct_conversation, save_message
            conv = get_or_create_direct_conversation(inviter.id, user.id)
            if conv:
                if conv.messages.count() == 0:
                    save_message(conv.id, inviter.id, f"Hey {user.username}! Welcome to OnlyUs.")
                    save_message(conv.id, user.id, "Thanks for the invitation! Happy to connect here.")
                
                n1 = Notification(
                    user_id=inviter.id,
                    title="Invitation Accepted",
                    message_hash=hash_text(f"{user.username} accepted invitation."),
                    type="system"
                )
                n2 = Notification(
                    user_id=user.id,
                    title="Connected with Friend",
                    message_hash=hash_text(f"Connected with {inviter.username}."),
                    type="system"
                )
                db.session.add_all([n1, n2])
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

def toggle_user_status(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    user.status = 'rejected' if user.status == 'approved' else 'approved'
    db.session.commit()
    return True, f"User {user.username} status set to {user.status}."

def suspend_user_account(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    user.status = 'suspended'
    db.session.commit()
    return True, f"Suspended account for {user.username}."

def deny_service_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    user.status = 'denied'
    db.session.commit()
    return True, f"Denied service access for {user.username}."

def notify_user_account(user_id, title, message):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    from blueprints.auth.security import hash_text
    msg_content = message or "Notification from Administrator."
    notif = Notification(
        user_id=user.id,
        title=title or "Admin Notice",
        message_hash=hash_text(msg_content),
        type="system"
    )
    db.session.add(notif)
    db.session.commit()
    return True, f"Notification sent to {user.username}."


def report_user_account(admin_id, user_id, reason="Admin Report"):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    rep = Report(
        reporter_id=admin_id,
        reported_user_id=user.id,
        reason=reason,
        status='pending'
    )
    db.session.add(rep)
    db.session.commit()
    
    from blueprints.auth.utils import send_report_email
    send_report_email(user.email, reported_item="User Account", reason=reason, report_id=f"REP-{rep.id}")
    return True, f"Report logged against {user.username}."

def message_user_as_admin(admin_id, user_id, message_text):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    from blueprints.chat.services import get_or_create_direct_conversation, save_message
    conv = get_or_create_direct_conversation(admin_id, user.id)
    if conv:
        save_message(conv.id, admin_id, message_text or "Hello from Administrator!")
        return True, f"Admin message dispatched to {user.username}."
    return False, "Could not open chat conversation."

def deny_user_invitation(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."
    # Revoke or reject invitations generated for this user
    invites = Invitation.query.filter_by(recipient_email=user.email).all()
    for inv in invites:
        inv.status = 'expired'
    db.session.commit()
    return True, f"Denied invitation permissions for {user.username}."

