from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from database.models import AuditLog
from database.db import db
from datetime import datetime, timedelta

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/log')
@login_required
def audit_log():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return render_template('errors/403.html'), 403
    
    page = request.args.get('page', 1, type=int)
    days = request.args.get('days', 7, type=int)
    user_filter = request.args.get('user_id', type=int)
    
    since_date = datetime.now() - timedelta(days=days)
    query = AuditLog.query.filter(AuditLog.created_at >= since_date)
    
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    
    # Get list of users for filter dropdown
    from database.models import User
    users = User.query.all()
    
    return render_template('audit/audit_log.html', logs=logs, users=users, days=days, selected_user=user_filter)

@audit_bp.route('/log/clear', methods=['POST'])
@login_required
def clear_old_logs():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('audit.audit_log'))
    
    days_to_keep = request.form.get('days_to_keep', 90, type=int)
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    deleted = AuditLog.query.filter(AuditLog.created_at < cutoff).delete()
    db.session.commit()
    flash(f'Deleted {deleted} old audit logs (older than {days_to_keep} days).', 'success')
    return redirect(url_for('audit.audit_log'))