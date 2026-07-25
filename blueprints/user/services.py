from extensions import db
from models import User, BlockedUser, Report, Notification

def block_user(blocker_id, blocked_id):
    if blocker_id == blocked_id:
        return False, "Cannot block yourself."
    
    existing = BlockedUser.query.filter_by(blocker_id=blocker_id, blocked_id=blocked_id).first()
    if existing:
        return True, "User already blocked."

    blocked = BlockedUser(blocker_id=blocker_id, blocked_id=blocked_id)
    db.session.add(blocked)
    db.session.commit()
    return True, "User blocked successfully."

def unblock_user(blocker_id, blocked_id):
    existing = BlockedUser.query.filter_by(blocker_id=blocker_id, blocked_id=blocked_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return True, "User unblocked successfully."
    return False, "Block record not found."

def submit_report(reporter_id, reported_user_id, reason):
    report = Report(reporter_id=reporter_id, reported_user_id=reported_user_id, reason=reason)
    db.session.add(report)
    db.session.commit()
    return report
