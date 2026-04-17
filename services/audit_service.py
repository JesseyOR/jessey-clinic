from database.models import AuditLog, User
from database.db import db
from datetime import datetime, timedelta

class AuditService:
    @staticmethod
    def log(user_id, action, details=None, ip_address=None):
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_user_logs(user_id, limit=100, offset=0):
        """Get audit logs for a specific user."""
        return AuditLog.query.filter_by(user_id=user_id)\
            .order_by(AuditLog.created_at.desc())\
            .offset(offset).limit(limit).all()
    
    @staticmethod
    def get_logs_by_action(action, days=7):
        """Get logs filtered by action type within last N days."""
        since = datetime.now() - timedelta(days=days)
        return AuditLog.query.filter(
            AuditLog.action == action,
            AuditLog.created_at >= since
        ).order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def get_recent_logs(limit=200):
        """Get most recent audit logs."""
        return AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_logs_by_date_range(start_date, end_date):
        """Get logs within date range."""
        return AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def delete_old_logs(days_to_keep=90):
        """Delete audit logs older than specified days."""
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        deleted = AuditLog.query.filter(AuditLog.created_at < cutoff).delete()
        db.session.commit()
        return deleted