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
        
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Retry with next generated ID if collision occurred
            new_id = generate_next_custom_user_id()
            user.id = new_id
            db.session.add(user)
            db.session.commit()
    else:
        user.status = 'approved'
        if req.password_hash:
            user.password_hash = req.password_hash
        if req.passcode:
            user.passcode = req.passcode
        db.session.commit()

    # Automatically initiate direct conversations between newly approved user and all existing active users
    try:
        active_users = User.query.filter(User.id != user.id, User.status == 'approved').all()
        from blueprints.auth.security import hash_text
        from blueprints.chat.services import get_or_create_direct_conversation, save_message
        
        for active_u in active_users:
            conv = get_or_create_direct_conversation(str(active_u.id), str(user.id))
            if conv and conv.messages.count() == 0:
                is_inviter = req.from_email and active_u.email.lower() == req.from_email.lower()
                if is_inviter:
                    save_message(conv.id, str(active_u.id), f"Hey {user.username}! Welcome to OnlyUs.")
                    save_message(conv.id, str(user.id), "Thanks for the invitation! Happy to connect here.")
                    n1 = Notification(
                        user_id=str(active_u.id),
                        title="Invitation Accepted",
                        message_hash=hash_text(f"{user.username} accepted invitation."),
                        type="system"
                    )
                    n2 = Notification(
                        user_id=str(user.id),
                        title="Connected with Friend",
                        message_hash=hash_text(f"Connected with {active_u.username}."),
                        type="system"
                    )
                    db.session.add_all([n1, n2])
                else:
                    save_message(conv.id, str(active_u.id), f"Hello {user.username}! Welcome to OnlyUs.")
        db.session.commit()
    except Exception as conv_err:
        print(f"[APPROVE CHAT INIT WARNING] {conv_err}")
        db.session.rollback()


    # Send Approval Email Notification
    try:
        send_approval_email(req.email)
        if req.for_email and req.for_email != req.email:
            send_approval_email(req.for_email)
    except Exception as mail_err:
        print(f"[APPROVE EMAIL WARNING] {mail_err}")

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
    recipient_email = (recipient_email or '').strip().lower()
    creator_id = str(creator_id)
    code = str(uuid.uuid4())
    passcode = passcode or generate_4digit_passcode()

    # Check if an invitation already exists for this email
    inv = Invitation.query.filter(Invitation.recipient_email.ilike(recipient_email)).first()
    if not inv:
        inv = Invitation(
            code=code,
            passcode=passcode,
            created_by_id=creator_id,
            recipient_email=recipient_email,
            status='pending'
        )
        db.session.add(inv)
    else:
        inv.code = code
        inv.passcode = passcode
        inv.created_by_id = creator_id
        inv.status = 'pending'
    
    # Also create or update pending AccountRequest
    creator = User.query.get(creator_id)
    sender_email = creator.email if creator else 'OnlyUs Admin'
    
    req = AccountRequest.query.filter(AccountRequest.email.ilike(recipient_email)).first()
    if not req:
        req = AccountRequest(
            email=recipient_email,
            from_email=sender_email,
            for_email=recipient_email,
            passcode=passcode,
            status='pending',
            note=f'Friend invitation from {sender_email}'
        )
        db.session.add(req)
    else:
        req.from_email = sender_email
        req.for_email = recipient_email
        req.passcode = passcode
        req.status = 'pending'

    db.session.commit()

    # Send email notification to friend safely
    try:
        send_friend_invite_email(recipient_email, sender_email, passcode)
    except Exception as e:
        print(f"[INVITE EMAIL WARNING] Could not send invite email: {e}")

    return inv


def _get_user_by_id(user_id):
    if not user_id:
        return None
    uid = str(user_id).strip()
    return User.query.get(uid) or User.query.filter(User.id == uid).first()

def update_user_role(user_id, new_role):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    user.role = new_role
    db.session.commit()
    return True, f"Updated {user.username}'s role to {new_role}."

def toggle_user_status(user_id):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    user.status = 'rejected' if user.status == 'approved' else 'approved'
    db.session.commit()
    return True, f"User {user.username} status set to {user.status}."

def suspend_user_account(user_id):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    user.status = 'suspended'
    db.session.commit()
    return True, f"Suspended account for {user.username}."

def deny_service_user(user_id):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    user.status = 'denied'
    db.session.commit()
    return True, f"Denied service access for {user.username}."

def notify_user_account(user_id, title, message):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    from blueprints.auth.security import hash_text
    msg_content = message or "Notification from Administrator."
    notif = Notification(
        user_id=str(user.id),
        title=title or "Admin Notice",
        message_hash=hash_text(msg_content),
        type="system"
    )
    db.session.add(notif)
    db.session.commit()
    return True, f"Notification sent to {user.username}."


def report_user_account(admin_id, user_id, reason="Admin Report"):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    rep = Report(
        reporter_id=str(admin_id),
        reported_user_id=str(user.id),
        reason=reason,
        status='pending'
    )
    db.session.add(rep)
    db.session.commit()
    
    from blueprints.auth.utils import send_report_email
    send_report_email(user.email, reported_item="User Account", reason=reason, report_id=f"REP-{rep.id}")
    return True, f"Report logged against {user.username}."

def message_user_as_admin(admin_id, user_id, message_text):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    from blueprints.chat.services import get_or_create_direct_conversation, save_message
    conv = get_or_create_direct_conversation(str(admin_id), str(user.id))
    if conv:
        save_message(conv.id, str(admin_id), message_text or "Hello from Administrator!")
        return True, f"Admin message dispatched to {user.username}."
    return False, "Could not open chat conversation."

def deny_user_invitation(user_id):
    user = _get_user_by_id(user_id)
    if not user:
        return False, "User not found."
    # Revoke or reject invitations generated for this user
    invites = Invitation.query.filter_by(recipient_email=user.email).all()
    for inv in invites:
        inv.status = 'expired'
    db.session.commit()
    return True, f"Denied invitation permissions for {user.username}."


