from flask import Blueprint, render_template
from flask_login import login_required, current_user

branch_bp = Blueprint('branches', __name__)

@branch_bp.route('/central-dashboard')
@login_required
def central_dashboard():
    if current_user.role != 'admin':
        return render_template('errors/403.html'), 403
    # Placeholder for multi-branch dashboard
    return render_template('branches/central_dashboard.html')

@branch_bp.route('/branch-stock')
@login_required
def branch_stock():
    # Placeholder for per-branch stock view
    return render_template('branches/branch_stock.html')

@branch_bp.route('/transfer-stock')
@login_required
def transfer_stock():
    if current_user.role != 'admin':
        return render_template('errors/403.html'), 403
    return render_template('branches/transfer_stock.html')