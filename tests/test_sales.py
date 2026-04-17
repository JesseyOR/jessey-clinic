import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from flask import Flask
from config import TestingConfig
from database.db import db
from database.models import Drug, User, Sale, SaleItem, Patient
from services.sales_service import SalesService
from services.stock_service import StockService

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username='cashier1', email='cashier@test.com', password='pass123', role='cashier')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_drug(app):
    with app.app_context():
        drug = Drug(
            name='Test Drug',
            selling_price=15.0,
            expiry_date=datetime.now().date() + timedelta(days=365),
            quantity=50,
            buying_price=8.0
        )
        db.session.add(drug)
        db.session.commit()
        return drug

@pytest.fixture
def test_patient(app):
    with app.app_context():
        patient = Patient(first_name='John', last_name='Doe', phone='123456')
        db.session.add(patient)
        db.session.commit()
        return patient

class TestSalesService:
    def test_create_sale_success(self, app, test_user, test_drug):
        with app.app_context():
            cart_items = [{'drug_id': test_drug.id, 'quantity': 2}]
            sale = SalesService.create_sale(
                cashier_id=test_user.id,
                cart_items=cart_items,
                payment_method='cash',
                ip_address='127.0.0.1'
            )
            assert sale is not None
            assert sale.total == 30.0  # 2 * 15
            assert sale.tax == 3.0  # 10% of 30
            # Check stock deduction
            updated_drug = Drug.query.get(test_drug.id)
            assert updated_drug.quantity == 48
    
    def test_create_sale_insufficient_stock(self, app, test_user, test_drug):
        with app.app_context():
            cart_items = [{'drug_id': test_drug.id, 'quantity': 100}]
            with pytest.raises(ValueError, match="Insufficient stock"):
                SalesService.create_sale(test_user.id, cart_items, 'cash')
    
    def test_create_sale_empty_cart(self, app, test_user):
        with app.app_context():
            with pytest.raises(ValueError, match="Cannot create empty sale"):
                SalesService.create_sale(test_user.id, [], 'cash')
    
    def test_create_sale_with_patient(self, app, test_user, test_drug, test_patient):
        with app.app_context():
            cart_items = [{'drug_id': test_drug.id, 'quantity': 1}]
            sale = SalesService.create_sale(
                cashier_id=test_user.id,
                cart_items=cart_items,
                payment_method='card',
                patient_id=test_patient.id,
                ip_address='127.0.0.1'
            )
            assert sale.patient_id == test_patient.id
    
    def test_get_sale_by_invoice(self, app, test_user, test_drug):
        with app.app_context():
            cart_items = [{'drug_id': test_drug.id, 'quantity': 1}]
            sale = SalesService.create_sale(test_user.id, cart_items, 'cash')
            fetched = SalesService.get_sale_by_invoice(sale.invoice_number)
            assert fetched.id == sale.id
    
    def test_sale_calculate_totals(self, app, test_user, test_drug):
        with app.app_context():
            sale = Sale(cashier_id=test_user.id, invoice_number='TEST001', payment_method='cash')
            db.session.add(sale)
            db.session.flush()
            item = SaleItem(test_drug, 3)
            sale.items.append(item)
            from flask import current_app
            sale.calculate_totals(0.10)
            assert sale.subtotal == 45.0
            assert sale.tax == 4.5
            assert sale.total == 49.5

class TestSaleModel:
    def test_sale_item_price_from_db(self, app, test_drug):
        with app.app_context():
            # Simulate malicious frontend sending wrong price - should be ignored
            item = SaleItem(test_drug, 2, unit_price=1.0)  # Trying to cheat
            assert item.unit_price == test_drug.selling_price  # Should use DB price
            assert item.total_price == test_drug.selling_price * 2