from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from database.db import db, Transaction
from database.models import User, AuditLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('auth/login.html')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated', 'danger')
                return render_template('auth/login.html')
            user.last_login = datetime.utcnow()
            with Transaction():
                db.session.add(user)
                audit = AuditLog(
                    user_id=user.id,
                    action='LOGIN_SUCCESS',
                    details=f"Logged in from {request.remote_addr}",
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            failed = AuditLog(
                user_id=None,
                action='LOGIN_FAILED',
                details=f"Failed login for username: {username} from {request.remote_addr}",
                ip_address=request.remote_addr
            )
            db.session.add(failed)
            db.session.commit()
            flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    audit = AuditLog(
        user_id=current_user.id,
        action='LOGOUT',
        details=f"Logged out from {request.remote_addr}",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if not old or not new:
            flash('All fields are required', 'danger')
        elif new != confirm:
            flash('New passwords do not match', 'danger')
        elif len(new) < 6:
            flash('Password must be at least 6 characters', 'danger')
        elif not current_user.check_password(old):
            flash('Current password is incorrect', 'danger')
        else:
            with Transaction():
                current_user.set_password(new)
                db.session.add(current_user)
                audit = AuditLog(
                    user_id=current_user.id,
                    action='PASSWORD_CHANGE',
                    details='Password changed',
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
            flash('Password changed successfully', 'success')
            return redirect(url_for('index'))
    return render_template('auth/change_password.html')