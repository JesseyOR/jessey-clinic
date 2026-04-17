from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access to specific roles.
    Usage: @role_required('admin', 'pharmacist')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required_custom(redirect_to='auth.login'):
    """
    Custom login required decorator with custom redirect.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for(redirect_to))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    """
    Decorator for granular permissions (future extension).
    Currently checks role-based permissions.
    """
    permission_map = {
        'manage_stock': ['admin', 'pharmacist'],
        'manage_users': ['admin'],
        'view_reports': ['admin', 'pharmacist'],
        'process_sales': ['admin', 'cashier'],
        'view_audit': ['admin']
    }
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in.', 'warning')
                return redirect(url_for('auth.login'))
            allowed_roles = permission_map.get(permission, [])
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator