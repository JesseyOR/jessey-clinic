from flask import request, g, current_app
from flask_login import current_user
from database.models import AuditLog
from database.db import db
import logging

logger = logging.getLogger(__name__)

class AuditMiddleware:
    """
    Middleware to automatically log all requests.
    """
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.log_request_start)
        app.after_request(self.log_request_end)
    
    def log_request_start(self):
        """Log the start of each request."""
        g.start_time = current_app.config.get('REQUEST_START_TIME')
        if current_user.is_authenticated:
            logger.info(f"Request started: {request.method} {request.path} by user {current_user.username}")
    
    def log_request_end(self, response):
        """Log the end of each request (success or failure)."""
        if hasattr(g, 'start_time'):
            duration = None
        if current_user.is_authenticated:
            # Only log POST, PUT, DELETE for audit (to reduce noise)
            if request.method in ['POST', 'PUT', 'DELETE']:
                try:
                    audit = AuditLog(
                        user_id=current_user.id,
                        action=f"HTTP_{request.method}",
                        details=f"{request.path} - Status: {response.status_code}",
                        ip_address=request.remote_addr
                    )
                    db.session.add(audit)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to log audit: {e}")
        return response

def log_request_middleware():
    """Simple function middleware to log every request."""
    if current_user.is_authenticated and request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        try:
            audit = AuditLog(
                user_id=current_user.id,
                action=f"REQUEST_{request.method}",
                details=f"{request.path}",
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Audit log failed: {e}")