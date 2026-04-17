from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database.models import Drug, Sale, SaleItem
from services.stock_service import StockService
from database.db import db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return render_template('errors/403.html'), 403
    today = datetime.now().date()
    today_sales = Sale.query.filter(db.func.date(Sale.created_at) == today).all()
    today_total = sum(s.total for s in today_sales)
    month_start = today.replace(day=1)
    month_sales = Sale.query.filter(Sale.created_at >= month_start).all()
    month_total = sum(s.total for s in month_sales)
    low_stock = StockService.get_low_stock_items()
    expiring = StockService.get_expiring_soon_items()
    expired = StockService.get_expired_items()
    stock_value = StockService.get_current_stock_value()
    thirty_days_ago = today - timedelta(days=30)
    top_drugs = db.session.query(
        Drug.name,
        db.func.sum(SaleItem.quantity).label('total_sold')
    ).join(SaleItem).join(Sale).filter(Sale.created_at >= thirty_days_ago)\
     .group_by(Drug.id).order_by(db.func.sum(SaleItem.quantity).desc()).limit(5).all()
    return render_template('dashboard/admin_dashboard.html',
        today_total=today_total,
        month_total=month_total,
        low_stock=low_stock,
        expiring_soon=expiring,
        expired=expired,
        stock_value=stock_value,
        top_drugs=top_drugs)

@dashboard_bp.route('/pharmacist')
@login_required
def pharmacist_dashboard():
    if current_user.role not in ['admin', 'pharmacist']:
        return render_template('errors/403.html'), 403
    low_stock = StockService.get_low_stock_items()
    expiring = StockService.get_expiring_soon_items()
    return render_template('dashboard/pharmacist_dashboard.html',
        low_stock=low_stock,
        expiring_soon=expiring)

@dashboard_bp.route('/cashier')
@login_required
def cashier_dashboard():
    today = datetime.now().date()
    my_sales = Sale.query.filter(
        db.func.date(Sale.created_at) == today,
        Sale.cashier_id == current_user.id
    ).all()
    my_total = sum(s.total for s in my_sales)
    return render_template('dashboard/cashier_dashboard.html',
        my_total_today=my_total,
        my_count_today=len(my_sales))