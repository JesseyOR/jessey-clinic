from database.db import db
from database.models import User, Drug, Supplier, Patient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def is_database_empty():
    """Check if database already contains any user."""
    return db.session.query(User).first() is None

def seed_database(force=False):
    """
    Seed database only if empty, unless force=True is passed.
    Returns True if seeded, False if already seeded.
    """
    if not force and not is_database_empty():
        logger.info("Database already contains data. Skipping seeding.")
        return False

    try:
        # Admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@jessey.com',
                password='admin123',
                role='admin'
            )
            db.session.add(admin)
            logger.info("Admin user created.")

        # Cashier user
        if not User.query.filter_by(username='cashier').first():
            cashier = User(
                username='cashier',
                email='cashier@jessey.com',
                password='cash123',
                role='cashier'
            )
            db.session.add(cashier)
            logger.info("Cashier user created.")

        # Sample supplier
        supplier = Supplier.query.filter_by(name='MedSource Ltd').first()
        if not supplier:
            supplier = Supplier(
                name='MedSource Ltd',
                contact_person='John Doe',
                phone='+1234567890',
                email='orders@medsource.com',
                address='123 Health Street'
            )
            db.session.add(supplier)
            db.session.flush()
            logger.info("Sample supplier created.")

        # Sample drugs
        if not Drug.query.filter_by(name='Paracetamol 500mg').first():
            drug1 = Drug(
                name='Paracetamol 500mg',
                selling_price=5.99,
                expiry_date=datetime.now().date() + timedelta(days=365),
                quantity=100,
                buying_price=3.50,
                category='Painkiller',
                supplier_id=supplier.id,
                requires_prescription=False
            )
            db.session.add(drug1)
            logger.info("Sample drug Paracetamol created.")

        if not Drug.query.filter_by(name='Amoxicillin 250mg').first():
            drug2 = Drug(
                name='Amoxicillin 250mg',
                selling_price=12.50,
                expiry_date=datetime.now().date() + timedelta(days=180),
                quantity=50,
                buying_price=8.00,
                category='Antibiotic',
                supplier_id=supplier.id,
                requires_prescription=True
            )
            db.session.add(drug2)
            logger.info("Sample drug Amoxicillin created.")

        # Sample patient
        if not Patient.query.filter_by(email='patient@example.com').first():
            patient = Patient(
                first_name='Test',
                last_name='Patient',
                phone='1234567890',
                email='patient@example.com',
                allergies='Penicillin'
            )
            db.session.add(patient)
            logger.info("Sample patient created.")

        db.session.commit()
        logger.info("Database seeding completed successfully.")
        return True

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Seeding failed: {e}")
        raise