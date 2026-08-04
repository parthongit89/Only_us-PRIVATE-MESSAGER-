from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Notification, BlockedUser, Report
from blueprints.auth.security import hash_text
from . import user_bp
from .services import block_user, unblock_user, submit_report

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        bio = request.form.get('bio')
        passcode = request.form.get('passcode')

        if username:
            current_user.username = username
        if bio is not None:
            current_user.bio = bio
        if passcode:
            current_user.passcode = passcode

        notif = Notification(user_id=current_user.id, title="Profile Updated", message_hash=hash_text("Profile updated."), type="activity")
        db.session.add(notif)

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('profile.html', user=current_user)

@user_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@user_bp.route('/notifications')
@login_required
def notifications():
    try:
        notifs = Notification.query.filter_by(user_id=str(current_user.id)).order_by(Notification.id.desc()).all()
        for n in notifs:
            n.is_read = True
        db.session.commit()
    except Exception as e:
        print(f"[NOTIFICATIONS ROUTE WARNING] {e}")
        db.session.rollback()
        try:
            notifs = Notification.query.filter_by(user_id=str(current_user.id)).all()
        except Exception:
            notifs = []
    return render_template('notifications.html', notifications=notifs)


@user_bp.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All notifications cleared.', 'success')
    return redirect(url_for('user.notifications'))

@user_bp.route('/blocked-users', methods=['GET', 'POST'])
@login_required
def blocked_users():
    if request.method == 'POST':
        target_id = request.form.get('target_user_id')
        action = request.form.get('action')
        if action == 'block':
            success, msg = block_user(current_user.id, target_id)
            if success:
                notif = Notification(user_id=current_user.id, title="Blocked User", message_hash=hash_text(msg), type="activity")
                db.session.add(notif)
                db.session.commit()
            flash(msg, 'info' if success else 'danger')
        elif action == 'unblock':
            success, msg = unblock_user(current_user.id, target_id)
            if success:
                notif = Notification(user_id=current_user.id, title="Unblocked User", message_hash=hash_text(msg), type="activity")
                db.session.add(notif)
                db.session.commit()
            flash(msg, 'success' if success else 'danger')
        return redirect(url_for('user.blocked_users'))

    blocks = BlockedUser.query.filter_by(blocker_id=current_user.id).all()
    all_users = User.query.filter(User.id != current_user.id, User.status == 'approved').all()
    return render_template('block.html', blocks=blocks, users=all_users)

@user_bp.route('/report-user', methods=['GET', 'POST'])
@login_required
def report_user():
    if request.method == 'POST':
        reported_id = request.form.get('reported_user_id')
        reason = request.form.get('reason')
        if reported_id and reason:
            submit_report(current_user.id, reported_id, reason)
            notif = Notification(user_id=current_user.id, title="Report Submitted", message_hash=hash_text("Report submitted."), type="activity")
            db.session.add(notif)
            db.session.commit()
            flash('Report submitted for review.', 'success')
            return redirect(url_for('user.profile'))
        flash('Reason and target user are required.', 'danger')

    users = User.query.filter(User.id != current_user.id).all()
    return render_template('report.html', users=users)

@user_bp.route('/invite', methods=['GET', 'POST'])
@login_required
def invite():
    from blueprints.admin.services import generate_invitation
    if request.method == 'POST':
        friend_email = request.form.get('email', '').strip().lower()
        if not friend_email:
            flash('Please enter a valid Gmail address.', 'danger')
            return redirect(url_for('user.invite'))

        if friend_email == current_user.email.lower():
            flash('You cannot send an invitation to your own email address.', 'warning')
            return redirect(url_for('user.invite'))

        existing_user = User.query.filter(User.email.ilike(friend_email)).first()
        if existing_user and existing_user.status == 'approved':
            flash(f'{friend_email} is already an active user on OnlyUs!', 'info')
            return redirect(url_for('user.invite'))

        try:
            inv = generate_invitation(current_user.id, friend_email)
            notif = Notification(user_id=current_user.id, title="Friend Invitation Sent", message_hash=hash_text(f"Invitation sent to {friend_email}."), type="activity")
            db.session.add(notif)
            db.session.commit()
            flash(f'Invitation sent successfully to {friend_email}! (Passcode: {inv.passcode})', 'success')
        except Exception as e:
            flash(f'Could not send invitation: {e}', 'danger')
        return redirect(url_for('user.invite'))

    return render_template('user_invite.html')


