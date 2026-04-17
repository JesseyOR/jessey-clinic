import os
import shutil
import sqlite3
from datetime import datetime
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class BackupService:
    @staticmethod
    def backup_database():
        """Create a backup of the SQLite database."""
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if not db_uri.startswith('sqlite:///'):
            logger.warning("Backup only supports SQLite for now")
            return None
        
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return None
        
        backup_dir = os.path.join(current_app.config['BASE_DIR'], 'backups', 'daily')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"jessey_clinic_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            # Use sqlite3 backup API for consistency
            source_conn = sqlite3.connect(db_path)
            dest_conn = sqlite3.connect(backup_path)
            source_conn.backup(dest_conn)
            source_conn.close()
            dest_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            
            # Delete old backups (keep last 30)
            BackupService._cleanup_old_backups(backup_dir, keep=30)
            
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    @staticmethod
    def _cleanup_old_backups(backup_dir, keep=30):
        """Delete old backup files, keeping only the most recent N."""
        try:
            files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')]
            files.sort(key=os.path.getmtime, reverse=True)
            for old_file in files[keep:]:
                os.remove(old_file)
                logger.info(f"Deleted old backup: {old_file}")
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    @staticmethod
    def manual_backup():
        """Create a manual backup in the manual folder."""
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if not db_uri.startswith('sqlite:///'):
            return None
        
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.exists(db_path):
            return None
        
        backup_dir = os.path.join(current_app.config['BASE_DIR'], 'backups', 'manual')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"manual_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Manual backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Manual backup failed: {e}")
            return None
    
    @staticmethod
    def restore_backup(backup_path):
        """Restore database from a backup file."""
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if not db_uri.startswith('sqlite:///'):
            return False
        
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Close existing connections (Flask will reconnect)
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    @staticmethod
    def list_backups():
        """List available backups in both daily and manual folders."""
        backups = []
        base_dir = current_app.config['BASE_DIR']
        backup_dirs = ['backups/daily', 'backups/manual']
        
        for rel_dir in backup_dirs:
            full_dir = os.path.join(base_dir, rel_dir)
            if os.path.exists(full_dir):
                for f in os.listdir(full_dir):
                    if f.endswith('.db'):
                        file_path = os.path.join(full_dir, f)
                        backups.append({
                            'name': f,
                            'path': file_path,
                            'type': 'daily' if 'daily' in rel_dir else 'manual',
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                        })
        
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups