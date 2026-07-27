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

    # Notify admins via in-app notification and email alert
    try:
        from blueprints.auth.utils import send_report_email, hash_text
        reporter = User.query.get(reporter_id)
        reported = User.query.get(reported_user_id)

        reporter_name = reporter.username if reporter else f"User {reporter_id}"
        reported_name = reported.username if reported else f"User {reported_user_id}"

        # Notify all admins in-app
        admins = User.query.filter(User.role.in_(['admin', 'owner'])).all()
        for a in admins:
            notif = Notification(
                user_id=a.id,
                title=f"🚨 New User Report: {reported_name}",
                message_hash=hash_text(f"Report by {reporter_name} on {reported_name}: {reason}"),
                type="activity"
            )
            db.session.add(notif)
        db.session.commit()

        # Send email alert to admin email
        send_report_email(
            to_email='sonavaneparth388@gmail.com',
            reported_item=f"User '{reported_name}' (Reported by {reporter_name})",
            reason=reason,
            report_id=f"REP-{report.id:04d}"
        )
    except Exception as e:
        print(f"[SUBMIT REPORT WARNING] {e}")

    return report

