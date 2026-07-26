from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import User, AccountRequest, Invitation, Report
from extensions import db
from . import admin_bp
from .services import (
    approve_request, reject_request, report_request,
    approve_all_requests, reject_all_requests,
    generate_invitation, update_user_role,
    toggle_user_status, suspend_user_account, deny_service_user,
    notify_user_account, report_user_account, message_user_as_admin,
    deny_user_invitation
)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin_or_owner:
            flash('Access restricted to Administrators and Owners.', 'danger')
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    requests_list = AccountRequest.query.filter_by(status='pending').order_by(AccountRequest.id.desc()).all()
    return render_template('admin_dashboard.html', requests=requests_list)

@admin_bp.route('/admin/requests/<int:req_id>/accept', methods=['POST'])
@login_required
@admin_required
def accept_request(req_id):
    success, msg = approve_request(req_id)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/requests/<int:req_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_req(req_id):
    success, msg = reject_request(req_id)
    flash(msg, 'info' if success else 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/requests/<int:req_id>/report', methods=['POST'])
@login_required
@admin_required
def report_req(req_id):
    success, msg = report_request(req_id)
    flash(msg, 'warning' if success else 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/requests/accept-all', methods=['POST'])
@login_required
@admin_required
def accept_all():
    count = approve_all_requests()
    flash(f'Accepted all {count} pending access requests.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/requests/reject-all', methods=['POST'])
@login_required
@admin_required
def reject_all():
    count = reject_all_requests()
    flash(f'Rejected all {count} pending access requests.', 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/users')
@login_required
@admin_required
def users_list():
    all_users = User.query.order_by(User.id.asc()).all()
    return render_template('admin_users.html', users=all_users)

@admin_bp.route('/admin/current-users')
@admin_bp.route('/admin/currentusers')
@login_required
@admin_required
def current_users():
    all_users = User.query.order_by(User.id.asc()).all()
    return render_template('Currentusers.html', users=all_users)

@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def user_toggle_status(user_id):
    success, msg = toggle_user_status(user_id)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/users/<int:user_id>/report', methods=['POST'])
@login_required
@admin_required
def user_report(user_id):
    reason = request.form.get('reason', 'Administrative report flag')
    success, msg = report_user_account(current_user.id, user_id, reason=reason)
    flash(msg, 'warning' if success else 'danger')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/users/<int:user_id>/notify', methods=['POST'])
@login_required
@admin_required
def user_notify(user_id):
    title = request.form.get('title', 'Admin Notification')
    message = request.form.get('message', 'Notice from Administrator.')
    success, msg = notify_user_account(user_id, title=title, message=message)
    flash(msg, 'info' if success else 'danger')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def user_suspend(user_id):
    success, msg = suspend_user_account(user_id)
    flash(msg, 'warning' if success else 'danger')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/users/<int:user_id>/deny-service', methods=['POST'])
@login_required
@admin_required
def user_deny_service(user_id):
    success, msg = deny_service_user(user_id)
    flash(msg, 'danger' if success else 'warning')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/users/<int:user_id>/message', methods=['POST'])
@login_required
@admin_required
def user_message(user_id):
    msg_text = request.form.get('message', 'Hello from Administrator!')
    success, msg = message_user_as_admin(current_user.id, user_id, msg_text)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/users/<int:user_id>/deny-invitation', methods=['POST'])
@login_required
@admin_required
def user_deny_invitation(user_id):
    success, msg = deny_user_invitation(user_id)
    flash(msg, 'info' if success else 'danger')
    return redirect(url_for('admin.current_users'))

@admin_bp.route('/admin/permit', methods=['GET', 'POST'])
@login_required
@admin_required
def permit():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_role = request.form.get('role')
        success, msg = update_user_role(user_id, new_role)
        flash(msg, 'success' if success else 'danger')
        return redirect(url_for('admin.permit'))

    all_users = User.query.order_by(User.id.asc()).all()
    return render_template('permit.html', users=all_users)

@admin_bp.route('/admin/invitation', methods=['GET', 'POST'])
@login_required
@admin_required
def invitation():
    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email')
        if recipient_email:
            inv = generate_invitation(current_user.id, recipient_email)
            flash(f'Generated invitation for {recipient_email}. Invite Code: {inv.code}', 'success')
            return redirect(url_for('admin.invitation'))
        flash('Recipient email is required.', 'danger')

    invites = Invitation.query.order_by(Invitation.id.desc()).all()
    return render_template('invitation.html', invitations=invites)
