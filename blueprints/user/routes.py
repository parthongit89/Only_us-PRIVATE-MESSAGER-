from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Notification, BlockedUser, Report
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
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).all()
    # Mark all as read
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

@user_bp.route('/blocked-users', methods=['GET', 'POST'])
@login_required
def blocked_users():
    if request.method == 'POST':
        target_id = request.form.get('target_user_id')
        action = request.form.get('action')
        if action == 'block':
            success, msg = block_user(current_user.id, target_id)
            flash(msg, 'info' if success else 'danger')
        elif action == 'unblock':
            success, msg = unblock_user(current_user.id, target_id)
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
        friend_email = request.form.get('email')
        if friend_email:
            try:
                inv = generate_invitation(current_user.id, friend_email)
                flash(f'Invitation sent to {friend_email} with 4-digit passcode ({inv.passcode})!', 'success')
            except Exception as e:
                flash(f'Could not send invitation: {e}', 'danger')
            return redirect(url_for('user.invite'))
        flash('Please enter a valid Gmail address.', 'danger')

    return render_template('user_invite.html')
