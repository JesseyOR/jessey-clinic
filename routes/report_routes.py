from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from database.models import Sale, SaleItem, Drug
from database.db import db
from datetime import datetime, timedelta

report_bp = Blueprint('reports', __name__)

@report_bp.route('/daily')
@login_required
def daily_report():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    sales = Sale.query.filter(db.func.date(Sale.created_at) == date).all()
    total = sum(s.total for s in sales)
    return render_template('reports/daily_report.html', date=date, total=total, sales=sales)

@report_bp.route('/monthly')
@login_required
def monthly_report():
    month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
    year, month = map(int, month_str.split('-'))
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year+1, 1, 1)
    else:
        end = datetime(year, month+1, 1)
    sales = Sale.query.filter(Sale.created_at >= start, Sale.created_at < end).all()
    total = sum(s.total for s in sales)
    return render_template('reports/monthly_report.html', month=month_str, total=total, sales=sales)

@report_bp.route('/top-products')
@login_required
def top_products():
    days = request.args.get('days', 30, type=int)
    since = datetime.now() - timedelta(days=days)
    top = db.session.query(
        Drug.name,
        db.func.sum(SaleItem.quantity).label('qty'),
        db.func.sum(SaleItem.total_price).label('revenue')
    ).join(SaleItem).join(Sale).filter(Sale.created_at >= since)\
     .group_by(Drug.id).order_by(db.func.sum(SaleItem.quantity).desc()).limit(10).all()
    slow = db.session.query(Drug.name, Drug.quantity)\
        .outerjoin(SaleItem).filter(SaleItem.id == None, Drug.quantity > 0).all()
    return render_template('reports/top_products.html', top=top, slow=slow, days=days)