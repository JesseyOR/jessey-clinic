import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from flask import Flask
from config import TestingConfig
from database.db import db, Transaction
from database.models import Drug, User, AuditLog
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
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username='testuser', email='test@test.com', password='test123', role='admin')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_drug(app):
    with app.app_context():
        drug = Drug(
            name='Test Paracetamol',
            selling_price=10.0,
            expiry_date=datetime.now().date() + timedelta(days=365),
            quantity=100,
            buying_price=5.0
        )
        db.session.add(drug)
        db.session.commit()
        return drug

class TestStockService:
    def test_deduct_stock_success(self, app, test_user, test_drug):
        with app.app_context():
            drug = StockService.deduct_stock(test_drug.id, 10, test_user.id, reason='TEST')
            assert drug.quantity == 90
    
    def test_deduct_stock_insufficient(self, app, test_user, test_drug):
        with app.app_context():
            with pytest.raises(ValueError, match="Insufficient stock"):
                StockService.deduct_stock(test_drug.id, 200, test_user.id, reason='TEST')
    
    def test_deduct_stock_invalid_quantity(self, app, test_user, test_drug):
        with app.app_context():
            with pytest.raises(ValueError, match="Quantity must be positive"):
                StockService.deduct_stock(test_drug.id, -5, test_user.id, reason='TEST')
    
    def test_add_stock_success(self, app, test_user, test_drug):
        with app.app_context():
            drug = StockService.add_stock(test_drug.id, 50, test_user.id, reason='TEST')
            assert drug.quantity == 150
    
    def test_low_stock_detection(self, app, test_user, test_drug):
        with app.app_context():
            test_drug.reorder_level = 20
            test_drug.quantity = 15
            db.session.commit()
            low_stock = StockService.get_low_stock_items()
            assert test_drug in low_stock
    
    def test_expiry_detection(self, app, test_user):
        with app.app_context():
            expired_drug = Drug(
                name='Expired Drug',
                selling_price=5.0,
                expiry_date=datetime.now().date() - timedelta(days=1),
                quantity=10
            )
            db.session.add(expired_drug)
            db.session.commit()
            expired_list = StockService.get_expired_items()
            assert expired_drug in expired_list

class TestDrugModel:
    def test_drug_validation_past_expiry(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Expiry date cannot be in the past"):
                Drug(
                    name='Bad Drug',
                    selling_price=10.0,
                    expiry_date=datetime.now().date() - timedelta(days=1)
                )
    
    def test_drug_deduct_method(self, app, test_drug):
        with app.app_context():
            test_drug.deduct_stock(30)
            assert test_drug.quantity == 70
            with pytest.raises(ValueError, match="Insufficient stock"):
                test_drug.deduct_stock(100)