from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from database.models import Drug, Sale, SaleItem, AuditLog
from services.stock_service import StockService
from services.report_service import ReportService
from database.db import db
from datetime import datetime, timedelta
import functools

mobile_api_bp = Blueprint('mobile_api', __name__, url_prefix='/api/mobile')

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Key')
        # Simple token validation - in production use proper JWT
        if not token or token != 'jessey-mobile-secret-key-2026':
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated

@mobile_api_bp.route('/stock/low')
@token_required
def mobile_low_stock():
    low = StockService.get_low_stock_items()
    return jsonify({
        'count': len(low),
        'items': [{
            'id': d.id,
            'name': d.name,
            'quantity': d.quantity,
            'reorder_level': d.reorder_level,
            'expiry_date': d.expiry_date.isoformat()
        } for d in low]
    })

@mobile_api_bp.route('/stock/expiring')
@token_required
def mobile_expiring_stock():
    expiring = StockService.get_expiring_soon_items()
    return jsonify({
        'count': len(expiring),
        'items': [{
            'id': d.id,
            'name': d.name,
            'quantity': d.quantity,
            'days_until_expiry': d.days_until_expiry,
            'expiry_date': d.expiry_date.isoformat()
        } for d in expiring]
    })

@mobile_api_bp.route('/sales/today')
@token_required
def mobile_sales_today():
    today = datetime.now().date()
    sales = Sale.query.filter(db.func.date(Sale.created_at) == today).all()
    total = sum(s.total for s in sales)
    count = len(sales)
    return jsonify({
        'date': today.isoformat(),
        'total_sales': total,
        'transaction_count': count,
        'average_ticket': total / count if count > 0 else 0
    })

@mobile_api_bp.route('/sales/weekly')
@token_required
def mobile_sales_weekly():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    daily_totals = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        day_sales = Sale.query.filter(db.func.date(Sale.created_at) == day).all()
        total = sum(s.total for s in day_sales)
        daily_totals.append({
            'date': day.isoformat(),
            'total': total
        })
    return jsonify({'weekly_sales': daily_totals})

@mobile_api_bp.route('/dashboard/summary')
@token_required
def mobile_dashboard_summary():
    today = datetime.now().date()
    today_sales = Sale.query.filter(db.func.date(Sale.created_at) == today).all()
    today_total = sum(s.total for s in today_sales)
    low_stock_count = len(StockService.get_low_stock_items())
    expiring_count = len(StockService.get_expiring_soon_items())
    expired_count = len(StockService.get_expired_items())
    return jsonify({
        'today_sales': today_total,
        'low_stock_alerts': low_stock_count,
        'expiring_soon_alerts': expiring_count,
        'expired_drugs': expired_count,
        'server_time': datetime.now().isoformat()
    })

@mobile_api_bp.route('/search/drugs')
@token_required
def mobile_search_drugs():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'error': 'Search query too short'}), 400
    drugs = Drug.query.filter(
        Drug.is_active == True,
        (Drug.name.contains(query) | Drug.generic_name.contains(query) | Drug.barcode == query)
    ).limit(20).all()
    return jsonify({
        'results': [{
            'id': d.id,
            'name': d.name,
            'selling_price': d.selling_price,
            'quantity': d.quantity,
            'requires_prescription': d.requires_prescription
        } for d in drugs]
    })