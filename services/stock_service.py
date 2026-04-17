from database.db import db, Transaction
from database.models import Drug, AuditLog
from flask import current_app
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class StockService:
    @staticmethod
    def deduct_stock(drug_id, quantity, user_id, sale_id=None, reason="SALE"):
        """
        Safely deduct stock with full transaction and validation.
        Returns the updated Drug object.
        """
        if quantity is None or quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        with Transaction():
            drug = Drug.query.filter_by(id=drug_id, is_active=True).first()
            if not drug:
                raise ValueError(f"Drug with id {drug_id} not found or inactive")
            
            # Check expiry before sale
            if drug.is_expired:
                raise ValueError(f"Cannot sell expired drug: {drug.name} (expired on {drug.expiry_date})")
            
            # Check stock
            if drug.quantity < quantity:
                raise ValueError(f"Insufficient stock for {drug.name}. Available: {drug.quantity}, Requested: {quantity}")
            
            # Perform deduction
            old_quantity = drug.quantity
            drug.deduct_stock(quantity)
            db.session.add(drug)
            
            # Audit log
            audit = AuditLog(
                user_id=user_id,
                action=f"STOCK_DEDUCT_{reason}",
                details=f"Deducted {quantity} units of {drug.name} (ID:{drug_id}). Old: {old_quantity}, New: {drug.quantity}. Sale ID: {sale_id}"
            )
            db.session.add(audit)
            
            # Log low stock warning
            if drug.is_low_stock:
                logger.warning(f"LOW STOCK ALERT: {drug.name} has {drug.quantity} units (threshold: {drug.reorder_level})")
            
            # Log expiry warning
            if drug.is_expiring_soon:
                logger.info(f"EXPIRING SOON: {drug.name} expires in {drug.days_until_expiry} days")
            
            return drug
    
    @staticmethod
    def add_stock(drug_id, quantity, user_id, supplier_id=None, batch_number=None,
                  buying_price=None, selling_price=None, expiry_date=None, reason="PURCHASE"):
        """
        Safely add stock with transaction.
        """
        if quantity is None or quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        with Transaction():
            drug = Drug.query.filter_by(id=drug_id).first()
            if not drug:
                raise ValueError(f"Drug with id {drug_id} not found")
            
            old_quantity = drug.quantity
            
            # Update optional fields if provided
            if batch_number:
                drug.batch_number = batch_number
            if buying_price is not None and buying_price > 0:
                drug.buying_price = buying_price
            if selling_price is not None and selling_price > 0:
                drug.selling_price = selling_price
            if expiry_date:
                from datetime import date
                if isinstance(expiry_date, str):
                    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                if expiry_date < date.today():
                    raise ValueError("Cannot add expired or backdated drug")
                drug.expiry_date = expiry_date
            if supplier_id:
                drug.supplier_id = supplier_id
            
            drug.add_stock(quantity)
            db.session.add(drug)
            
            audit = AuditLog(
                user_id=user_id,
                action=f"STOCK_ADD_{reason}",
                details=f"Added {quantity} units to {drug.name}. Old: {old_quantity}, New: {drug.quantity}. Supplier ID: {supplier_id}"
            )
            db.session.add(audit)
            
            return drug
    
    @staticmethod
    def get_low_stock_items():
        """Return all drugs with stock <= reorder_level."""
        return Drug.query.filter(
            Drug.is_active == True,
            Drug.quantity <= Drug.reorder_level
        ).order_by(Drug.quantity.asc()).all()
    
    @staticmethod
    def get_expiring_soon_items():
        """Return drugs expiring within configured warning days."""
        threshold = current_app.config.get('EXPIRY_WARNING_DAYS', 30)
        today = datetime.now().date()
        expiry_limit = today + timedelta(days=threshold)
        return Drug.query.filter(
            Drug.is_active == True,
            Drug.expiry_date <= expiry_limit,
            Drug.expiry_date > today
        ).order_by(Drug.expiry_date.asc()).all()
    
    @staticmethod
    def get_expired_items():
        """Return all expired drugs."""
        today = datetime.now().date()
        return Drug.query.filter(
            Drug.is_active == True,
            Drug.expiry_date < today
        ).order_by(Drug.expiry_date.asc()).all()
    
    @staticmethod
    def get_current_stock_value():
        """Calculate total stock value based on buying price."""
        result = db.session.query(db.func.sum(Drug.quantity * Drug.buying_price)).filter(Drug.is_active == True).scalar()
        return result or 0.0
    
    @staticmethod
    def get_current_stock_selling_value():
        """Calculate total potential revenue based on selling price."""
        result = db.session.query(db.func.sum(Drug.quantity * Drug.selling_price)).filter(Drug.is_active == True).scalar()
        return result or 0.0