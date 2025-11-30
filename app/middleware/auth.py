"""
Authentication middleware for route protection
"""
from functools import wraps
from flask import request, jsonify, redirect, url_for
from flask_login import current_user

def login_required_api(f):
    """API route decorator that requires authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # If it's an API request (JSON expected), return JSON error
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            # Otherwise redirect to login
            return redirect(url_for('auth.login'))
        
        # Check if account is active
        if not current_user.is_active:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Account is deactivated'}), 403
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def email_verified_required(f):
    """Decorator that requires email to be verified"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        if not current_user.email_verified:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Email verification required'}), 403
            # Could redirect to verification page
            return redirect(url_for('auth.verify_email'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator that requires admin role (if you implement roles)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # For now, is_verified can serve as admin check, or add role field
        if not current_user.is_verified:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


