#!/usr/bin/env python
"""
Automated daily backup script.
Run via cron or scheduled task.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.backup_service import BackupService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting daily backup...")
    try:
        backup_path = BackupService.backup_database()
        if backup_path:
            logger.info(f"Backup successful: {backup_path}")
        else:
            logger.error("Backup failed")
    except Exception as e:
        logger.exception(f"Backup error: {e}")

if __name__ == '__main__':
    main()