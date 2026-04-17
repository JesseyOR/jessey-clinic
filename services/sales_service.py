from database.db import db, Transaction
from database.models import Sale, SaleItem, Drug, Patient, AuditLog
from services.stock_service import StockService
from flask import current_app
from datetime import datetime
import uuid

class SalesService:
    @staticmethod
    def create_sale(cashier_id, cart_items, payment_method='cash', patient_id=None, discount=0.0, ip_address=None):
        """
        Create a complete sale with stock deduction.
        cart_items: list of dicts [{'drug_id': 1, 'quantity': 2}, ...]
        Returns the Sale object.
        """
        if not cart_items:
            raise ValueError("Cannot create empty sale")
        
        # Validate all items first
        for item in cart_items:
            if item.get('quantity', 0) <= 0:
                raise ValueError(f"Invalid quantity for drug {item.get('drug_id')}")
        
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        with Transaction():
            # Create sale record
            sale = Sale(cashier_id, invoice_number, payment_method, patient_id)
            sale.discount = discount
            db.session.add(sale)
            db.session.flush()  # Get sale.id
            
            # Process each item
            for item in cart_items:
                drug = Drug.query.get(item['drug_id'])
                if not drug:
                    raise ValueError(f"Drug with ID {item['drug_id']} not found")
                if not drug.is_active:
                    raise ValueError(f"Drug {drug.name} is inactive")
                if drug.is_expired:
                    raise ValueError(f"Cannot sell expired drug: {drug.name}")
                if drug.requires_prescription:
                    # Check if prescription exists for this patient and drug
                    if patient_id:
                        from database.models import Prescription
                        valid_rx = Prescription.query.filter(
                            Prescription.patient_id == patient_id,
                            Prescription.drug_id == drug.id,
                            Prescription.expiry_date >= datetime.now().date()
                        ).first()
                        if not valid_rx:
                            raise ValueError(f"Valid prescription required for {drug.name}")
                    else:
                        raise ValueError(f"Prescription required for {drug.name}. Please attach patient.")
                
                # Add sale item
                sale_item = SaleItem(drug, item['quantity'])
                sale.items.append(sale_item)
                
                # Deduct stock
                StockService.deduct_stock(drug.id, item['quantity'], cashier_id, sale.id, "SALE")
            
            # Calculate totals
            sale.calculate_totals(current_app.config['TAX_RATE'])
            db.session.add(sale)
            
            # Audit log
            audit = AuditLog(
                user_id=cashier_id,
                action='SALE_CREATED',
                details=f"Sale {invoice_number}: {len(cart_items)} items, total ${sale.total:.2f}",
                ip_address=ip_address
            )
            db.session.add(audit)
            
            return sale
    
    @staticmethod
    def get_sale_by_invoice(invoice_number):
        return Sale.query.filter_by(invoice_number=invoice_number).first()
    
    @staticmethod
    def get_sales_by_cashier(cashier_id, limit=100):
        return Sale.query.filter_by(cashier_id=cashier_id).order_by(Sale.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_sales_by_date_range(start_date, end_date):
        return Sale.query.filter(
            Sale.created_at >= start_date,
            Sale.created_at <= end_date
        ).order_by(Sale.created_at.desc()).all()
    
    @staticmethod
    def return_sale(sale_id, user_id, reason="RETURN", ip_address=None):
        """
        Process a return: reverse stock and mark sale as returned.
        """
        with Transaction():
            sale = Sale.query.get(sale_id)
            if not sale:
                raise ValueError("Sale not found")
            if sale.payment_status == 'returned':
                raise ValueError("Sale already returned")
            
            # Restore stock for each item
            for item in sale.items:
                drug = Drug.query.get(item.drug_id)
                if drug:
                    drug.add_stock(item.quantity)
                    db.session.add(drug)
            
            # Mark sale as returned
            sale.payment_status = 'returned'
            db.session.add(sale)
            
            audit = AuditLog(
                user_id=user_id,
                action='SALE_RETURNED',
                details=f"Returned sale {sale.invoice_number}. Reason: {reason}",
                ip_address=ip_address
            )
            db.session.add(audit)
            
            return sale