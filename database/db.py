from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import logging

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created/verified.")

class Transaction:
    """Context manager for safe database transactions."""
    def __enter__(self):
        return db.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logging.error(f"Transaction commit failed: {e}")
                raise
        else:
            db.session.rollback()
            logging.error(f"Transaction rolled back: {exc_val}")
            return False  # Propagate exception

def safe_commit():
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Commit failed: {e}")
        raise