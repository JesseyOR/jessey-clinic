from database.models import Sale, SaleItem, Drug, User
from database.db import db
from datetime import datetime, timedelta

class ReportService:
    @staticmethod
    def get_daily_sales(date):
        """Get sales summary for a specific date."""
        sales = Sale.query.filter(db.func.date(Sale.created_at) == date).all()
        total = sum(s.total for s in sales)
        tax_total = sum(s.tax for s in sales)
        discount_total = sum(s.discount for s in sales)
        return {
            'date': date,
            'total_sales': total,
            'tax_total': tax_total,
            'discount_total': discount_total,
            'transaction_count': len(sales),
            'average_ticket': total / len(sales) if sales else 0,
            'sales': sales
        }
    
    @staticmethod
    def get_monthly_profit(year, month):
        """Calculate profit for a given month."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year+1, 1, 1)
        else:
            end_date = datetime(year, month+1, 1)
        
        sales = Sale.query.filter(Sale.created_at >= start_date, Sale.created_at < end_date).all()
        total_revenue = sum(s.total for s in sales)
        
        # Calculate cost of goods sold
        cost_result = db.session.query(
            db.func.sum(SaleItem.quantity * Drug.buying_price)
        ).join(Drug).join(Sale).filter(
            Sale.created_at >= start_date,
            Sale.created_at < end_date
        ).scalar()
        cost_of_goods = cost_result or 0.0
        
        profit = total_revenue - cost_of_goods
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'year': year,
            'month': month,
            'total_revenue': total_revenue,
            'cost_of_goods': cost_of_goods,
            'profit': profit,
            'profit_margin': profit_margin,
            'transaction_count': len(sales)
        }
    
    @staticmethod
    def get_top_products(days=30, limit=10):
        """Get best selling products by quantity."""
        since = datetime.now() - timedelta(days=days)
        results = db.session.query(
            Drug.id,
            Drug.name,
            Drug.category,
            db.func.sum(SaleItem.quantity).label('total_quantity'),
            db.func.sum(SaleItem.total_price).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= since
        ).group_by(Drug.id).order_by(
            db.func.sum(SaleItem.quantity).desc()
        ).limit(limit).all()
        
        return [{
            'id': r.id,
            'name': r.name,
            'category': r.category,
            'quantity_sold': r.total_quantity,
            'revenue': r.total_revenue
        } for r in results]
    
    @staticmethod
    def get_slow_moving_products(days=60):
        """Get products with no sales in the given period."""
        since = datetime.now() - timedelta(days=days)
        sold_subquery = db.session.query(SaleItem.drug_id).join(Sale).filter(
            Sale.created_at >= since
        ).distinct().subquery()
        
        slow_products = Drug.query.filter(
            Drug.is_active == True,
            Drug.id.notin_(sold_subquery),
            Drug.quantity > 0
        ).order_by(Drug.quantity.desc()).all()
        
        return slow_products
    
    @staticmethod
    def get_cashier_performance(start_date, end_date):
        """Get sales performance per cashier."""
        results = db.session.query(
            User.id,
            User.username,
            db.func.count(Sale.id).label('transaction_count'),
            db.func.sum(Sale.total).label('total_sales'),
            db.func.avg(Sale.total).label('average_ticket')
        ).join(Sale).filter(
            Sale.created_at >= start_date,
            Sale.created_at <= end_date
        ).group_by(User.id).all()
        
        return [{
            'cashier_id': r.id,
            'username': r.username,
            'transaction_count': r.transaction_count,
            'total_sales': r.total_sales or 0,
            'average_ticket': r.average_ticket or 0
        } for r in results]
    
    @staticmethod
    def get_inventory_summary():
        """Get overall inventory metrics."""
        total_products = Drug.query.filter_by(is_active=True).count()
        total_units = db.session.query(db.func.sum(Drug.quantity)).filter(Drug.is_active == True).scalar() or 0
        low_stock_count = Drug.query.filter(Drug.is_active == True, Drug.quantity <= Drug.reorder_level).count()
        expiring_soon_count = 0
        from datetime import date
        from flask import current_app
        threshold = current_app.config.get('EXPIRY_WARNING_DAYS', 30)
        expiry_limit = date.today() + timedelta(days=threshold)
        expiring_soon_count = Drug.query.filter(
            Drug.is_active == True,
            Drug.expiry_date <= expiry_limit,
            Drug.expiry_date > date.today()
        ).count()
        expired_count = Drug.query.filter(Drug.is_active == True, Drug.expiry_date < date.today()).count()
        
        return {
            'total_products': total_products,
            'total_units': total_units,
            'low_stock_count': low_stock_count,
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count
        }