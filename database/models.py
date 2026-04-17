from database.db import db
from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import re

# ---------- Validators ----------
def validate_positive_int(value, field):
    if value is None:
        raise ValueError(f"{field} cannot be None")
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} cannot be negative")
    return value

def validate_positive_float(value, field):
    if value is None:
        raise ValueError(f"{field} cannot be None")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    if value < 0:
        raise ValueError(f"{field} cannot be negative")
    return float(value)

def validate_string(value, field, min_len=1, max_len=200, allow_none=False):
    if allow_none and value is None:
        return None
    if value is None:
        raise ValueError(f"{field} cannot be None")
    value = str(value).strip()
    if len(value) < min_len:
        raise ValueError(f"{field} too short (min {min_len})")
    if len(value) > max_len:
        raise ValueError(f"{field} too long (max {max_len})")
    return value

def validate_email(email):
    if not email:
        return None
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format")
    return email.lower()

# ---------- Models ----------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='cashier')
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    sales = db.relationship('Sale', backref='cashier', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def __init__(self, username, email, password, role='cashier'):
        self.username = validate_string(username, 'Username', 3, 80)
        self.email = validate_email(email)
        self.role = validate_string(role, 'Role', 2, 50)
        self.set_password(password)
        self.is_active = True

    def set_password(self, password):
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) if password else False

    def __repr__(self):
        return f'<User {self.username}>'

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20), index=True)
    email = db.Column(db.String(120), index=True)
    address = db.Column(db.String(300))
    outstanding_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    drugs = db.relationship('Drug', backref='supplier', lazy=True)

    def __init__(self, name, contact_person=None, phone=None, email=None, address=None):
        self.name = validate_string(name, 'Supplier name', 2, 200)
        self.contact_person = validate_string(contact_person, 'Contact person', 2, 100, allow_none=True)
        self.phone = phone.strip() if phone else None
        self.email = validate_email(email) if email else None
        self.address = address.strip() if address else None
        self.outstanding_balance = 0.0

class Drug(db.Model):
    __tablename__ = 'drugs'
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(100), unique=True, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    generic_name = db.Column(db.String(200))
    category = db.Column(db.String(100), index=True)

    quantity = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=20, nullable=False)

    buying_price = db.Column(db.Float, default=0.0, nullable=False)
    selling_price = db.Column(db.Float, default=0.0, nullable=False)

    expiry_date = db.Column(db.Date, nullable=False)
    manufactured_date = db.Column(db.Date)
    batch_number = db.Column(db.String(100))

    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), index=True)
    requires_prescription = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sale_items = db.relationship('SaleItem', backref='drug', lazy=True)
    prescriptions = db.relationship('Prescription', backref='drug', lazy=True)

    def __init__(self, name, selling_price, expiry_date, quantity=0, buying_price=0.0,
                 barcode=None, generic_name=None, category=None, reorder_level=None,
                 supplier_id=None, requires_prescription=False, batch_number=None,
                 manufactured_date=None):
        self.name = validate_string(name, 'Drug name', 2, 200)
        self.selling_price = validate_positive_float(selling_price, 'Selling price')
        self.buying_price = validate_positive_float(buying_price, 'Buying price')
        if not isinstance(expiry_date, date):
            raise ValueError("expiry_date must be a date object")
        if expiry_date < datetime.now().date():
            raise ValueError("Expiry date cannot be in the past")
        self.expiry_date = expiry_date
        self.quantity = validate_positive_int(quantity, 'Quantity')
        self.barcode = barcode.strip() if barcode else None
        self.generic_name = generic_name.strip() if generic_name else None
        self.category = category.strip() if category else None
        self.reorder_level = reorder_level if reorder_level is not None else 20
        self.supplier_id = supplier_id
        self.requires_prescription = requires_prescription
        self.batch_number = batch_number.strip() if batch_number else None
        self.manufactured_date = manufactured_date
        self.is_active = True

    def deduct_stock(self, qty):
        qty = validate_positive_int(qty, 'Deduction quantity')
        if self.quantity < qty:
            raise ValueError(f"Insufficient stock: have {self.quantity}, need {qty}")
        self.quantity -= qty
        return self.quantity

    def add_stock(self, qty):
        qty = validate_positive_int(qty, 'Addition quantity')
        self.quantity += qty
        return self.quantity

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def days_until_expiry(self):
        return (self.expiry_date - datetime.now().date()).days

    @property
    def is_expired(self):
        return self.expiry_date < datetime.now().date()

    @property
    def is_expiring_soon(self):
        from flask import current_app
        threshold = current_app.config['EXPIRY_WARNING_DAYS']
        return 0 < self.days_until_expiry <= threshold

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False, index=True)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(20), index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    allergies = db.Column(db.Text)
    blood_type = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales = db.relationship('Sale', backref='patient', lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)

    def __init__(self, first_name, last_name, phone=None, email=None, date_of_birth=None,
                 gender=None, allergies=None, blood_type=None):
        self.first_name = validate_string(first_name, 'First name', 1, 100)
        self.last_name = validate_string(last_name, 'Last name', 1, 100)
        self.phone = phone.strip() if phone else None
        self.email = validate_email(email) if email else None
        self.date_of_birth = date_of_birth
        self.gender = gender.strip() if gender else None
        self.allergies = allergies.strip() if allergies else None
        self.blood_type = blood_type.strip().upper() if blood_type else None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), index=True)

    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    tax = db.Column(db.Float, default=0.0, nullable=False)
    discount = db.Column(db.Float, default=0.0, nullable=False)
    total = db.Column(db.Float, default=0.0, nullable=False)

    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(50), default='completed')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

    def __init__(self, cashier_id, invoice_number, payment_method='cash', patient_id=None):
        self.cashier_id = cashier_id
        self.invoice_number = validate_string(invoice_number, 'Invoice number', 3, 50)
        self.payment_method = validate_string(payment_method, 'Payment method', 2, 50)
        self.patient_id = patient_id

    def calculate_totals(self, tax_rate):
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax = self.subtotal * tax_rate
        self.total = self.subtotal + self.tax - self.discount

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False, index=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)  # from DB, not frontend
    total_price = db.Column(db.Float, nullable=False)

    def __init__(self, drug, quantity, unit_price=None):
        self.drug_id = drug.id
        self.quantity = validate_positive_int(quantity, 'Quantity')
        self.unit_price = unit_price if unit_price is not None else drug.selling_price
        self.total_price = self.unit_price * self.quantity

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), index=True)
    doctor_name = db.Column(db.String(200))
    prescription_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    image_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, patient_id, drug_id, doctor_name=None, prescription_date=None,
                 expiry_date=None, image_path=None, sale_id=None):
        self.patient_id = patient_id
        self.drug_id = drug_id
        self.doctor_name = validate_string(doctor_name, 'Doctor name', 2, 200, allow_none=True)
        self.prescription_date = prescription_date or datetime.now().date()
        self.expiry_date = expiry_date
        self.image_path = image_path
        self.sale_id = sale_id

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __init__(self, user_id, action, details=None, ip_address=None):
        self.user_id = user_id
        self.action = validate_string(action, 'Action', 1, 200)
        self.details = details
        self.ip_address = ip_address