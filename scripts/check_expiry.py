#!/usr/bin/env python
"""
Check for expired and expiring drugs daily.
Sends alerts (can be extended to email/SMS).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stock_service import StockService
from database.db import db
from database.models import AuditLog
from flask import Flask
from config import ActiveConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_expiry_check():
    app = Flask(__name__)
    app.config.from_object(ActiveConfig)
    db.init_app(app)
    
    with app.app_context():
        expired = StockService.get_expired_items()
        expiring = StockService.get_expiring_soon_items()
        
        if expired:
            logger.warning(f"Found {len(expired)} expired drugs")
            for drug in expired:
                logger.warning(f"EXPIRED: {drug.name} (expired {drug.expiry_date})")
                # Log to audit
                audit = AuditLog(
                    user_id=None,
                    action='SYSTEM_EXPIRY_ALERT',
                    details=f"Drug {drug.name} (ID:{drug.id}) expired on {drug.expiry_date}"
                )
                db.session.add(audit)
        
        if expiring:
            logger.info(f"Found {len(expiring)} drugs expiring soon")
            for drug in expiring:
                logger.info(f"EXPIRING SOON: {drug.name} expires in {drug.days_until_expiry} days")
        
        db.session.commit()
        logger.info("Expiry check completed")

if __name__ == '__main__':
    run_expiry_check()