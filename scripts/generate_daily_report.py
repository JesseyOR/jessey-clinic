#!/usr/bin/env python
"""
Generate and save daily sales report.
Can be run via cron at midnight.
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_service import ReportService
from services.backup_service import BackupService
from database.db import db
from flask import Flask
from config import ActiveConfig
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_daily_report():
    app = Flask(__name__)
    app.config.from_object(ActiveConfig)
    db.init_app(app)
    
    with app.app_context():
        yesterday = datetime.now().date() - timedelta(days=1)
        report = ReportService.get_daily_sales(yesterday)
        
        # Save as JSON
        reports_dir = os.path.join(app.config['BASE_DIR'], 'reports_archive')
        os.makedirs(reports_dir, exist_ok=True)
        
        report_data = {
            'date': report['date'].isoformat(),
            'total_sales': report['total_sales'],
            'tax_total': report['tax_total'],
            'discount_total': report['discount_total'],
            'transaction_count': report['transaction_count'],
            'average_ticket': report['average_ticket'],
            'transactions': [
                {
                    'invoice': s.invoice_number,
                    'time': s.created_at.isoformat(),
                    'cashier': s.cashier.username,
                    'total': s.total
                }
                for s in report['sales']
            ]
        }
        
        filename = f"daily_report_{yesterday.strftime('%Y%m%d')}.json"
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Daily report saved: {filepath}")
        
        # Also print summary
        logger.info(f"SUMMARY for {yesterday}: ${report['total_sales']:.2f} from {report['transaction_count']} transactions")
        
        return report_data

if __name__ == '__main__':
    generate_daily_report()