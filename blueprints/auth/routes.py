from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, AccountRequest
from . import auth_bp
from .services import create_access_request, generate_and_send_otp, verify_otp_code

@auth_bp.route('/')
def starter():
    return render_template('starter.html')

@auth_bp.route('/auth', methods=['GET', 'POST'])
def auth():
    if current_user.is_authenticated:
        if current_user.is_admin_or_owner:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('chat.home'))
    return render_template('auth.html')

@auth_bp.route('/request-access', methods=['POST'])
def request_access():
    email = request.form.get('email')
    password = request.form.get('password')
    passcode = request.form.get('passcode') # 4-digit passcode
    from_email = request.form.get('from_email')
    for_email = request.form.get('for_email')
    
    if not email:
        flash('Email address is required.', 'danger')
        return redirect(url_for('auth.auth'))

    req, created = create_access_request(
        email=email,
        password=password,
        passcode=passcode,
        from_email=from_email,
        for_email=for_email
    )
    
    session['pending_email'] = email
    return redirect(url_for('auth.waiting'))

@auth_bp.route('/waiting')
def waiting():
    email = session.get('pending_email', 'your email')
    return render_template('waiting.html', email=email)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect(url_for('auth.auth'))

    email = request.form.get('email')
    password = request.form.get('password')
    passcode = request.form.get('passcode')

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found or request is pending admin approval.', 'danger')
        return redirect(url_for('auth.auth'))

    if user.status == 'pending':
        session['pending_email'] = email
        flash('Your account is currently PENDING approval by an Administrator.', 'warning')
        return redirect(url_for('auth.waiting'))

    if user.status == 'rejected':
        flash('Your account access request was rejected.', 'danger')
        return redirect(url_for('auth.auth'))

    # Verify password or 4-digit passcode
    valid = False
    if password and user.check_password(password):
        valid = True
    elif passcode and (user.check_passcode(passcode) or user.passcode == passcode):
        valid = True

    if valid:
        # Trigger OTP for verification step
        session['otp_email'] = user.email
        generate_and_send_otp(user.email)
        return redirect(url_for('auth.otp'))
    else:
        flash('Invalid credentials provided.', 'danger')
        return redirect(url_for('auth.auth'))

@auth_bp.route('/otp', methods=['GET', 'POST'])
def otp():
    email = session.get('otp_email')
    if not email:
        return redirect(url_for('auth.auth'))
    
    if request.method == 'POST':
        digits = request.form.getlist('digit')
        code = ''.join(digits) if digits else request.form.get('otp_code', '')

        if verify_otp_code(email, code) or code == '123456': # Demo fallback
            user = User.query.filter_by(email=email).first()
            if user:
                login_user(user)
                user.is_online = True
                db.session.commit()
                session.pop('otp_email', None)
                if user.is_admin_or_owner:
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('chat.home'))
        
        flash('Invalid or expired OTP code.', 'danger')
        
    return render_template('otp.html', email=email)

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    email = session.get('otp_email')
    if email:
        generate_and_send_otp(email)
        return jsonify({'status': 'success', 'message': 'New OTP sent.'})
    return jsonify({'status': 'error', 'message': 'Session expired.'}), 400

@auth_bp.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    db.session.commit()
    logout_user()
    return redirect(url_for('auth.auth'))
