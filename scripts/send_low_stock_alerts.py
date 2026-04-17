#!/usr/bin/env python
"""
Send low stock alerts via email (configure SMTP in .env to enable).
"""
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stock_service import StockService
from database.db import db
from flask import Flask
from config import ActiveConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_email_alert(low_stock_items):
    """Send email alert (SMTP settings required)."""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT', 587)
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    alert_email = os.getenv('ALERT_EMAIL')
    
    if not all([smtp_server, smtp_user, smtp_password, alert_email]):
        logger.warning("Email settings missing, skipping email alert")
        return
    
    subject = f"LOW STOCK ALERT - {len(low_stock_items)} items below reorder level"
    body = "The following drugs are low in stock:\n\n"
    for drug in low_stock_items:
        body += f"- {drug.name}: {drug.quantity} units (reorder at {drug.reorder_level})\n"
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = alert_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info("Email alert sent")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

def run_alert():
    app = Flask(__name__)
    app.config.from_object(ActiveConfig)
    db.init_app(app)
    
    with app.app_context():
        low_stock = StockService.get_low_stock_items()
        if low_stock:
            logger.info(f"Found {len(low_stock)} low stock items")
            send_email_alert(low_stock)
        else:
            logger.info("No low stock items")

if __name__ == '__main__':
    run_alert()