"""
RESTful API endpoints for authentication
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import re

from app.extension import db
from app.models.users import User
from app.models.user_settings import UserSettings
from app.lib.auth import generate_token, token_required, api_login_required, generate_verification_token, generate_reset_token
from app.lib.email import send_verification_email, send_password_reset_email

auth_api = Blueprint("auth_api", __name__, url_prefix="/api/auth")

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format (alphanumeric and underscore, 5-30 chars)"""
    pattern = r'^[a-zA-Z0-9_]{5,30}$'
    return re.match(pattern, username) is not None

@auth_api.route("/register", methods=["POST"])
def register():
    """POST /api/auth/register - Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    fullname = data.get('fullname', '').strip()
    
    errors = []
    
    # Validate username
    if not username:
        errors.append('Username is required')
    elif not validate_username(username):
        errors.append('Username must be 5-30 characters, alphanumeric and underscores only')
    elif User.query.filter_by(username=username).first():
        errors.append('Username already exists')
    
    # Validate email
    if not email:
        errors.append('Email is required')
    elif not validate_email(email):
        errors.append('Invalid email format')
    elif User.query.filter_by(email=email).first():
        errors.append('Email already exists')
    
    # Validate password
    if not password:
        errors.append('Password is required')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters')
    
    # Validate fullname
    if not fullname:
        errors.append('Full name is required')
    elif len(fullname) < 2 or len(fullname) > 32:
        errors.append('Full name must be 2-32 characters')
    
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Create user
        verification_token = generate_verification_token()
        user = User(
            username=username,
            email=email,
            fullname=fullname,
            password=generate_password_hash(password),
            email_verification_token=verification_token,
            email_verified=False,
            is_private=False,
            is_active=True
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create default user settings
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        
        db.session.commit()
        
        # Send verification email
        send_verification_email(user)
        
        # Generate JWT token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Registration successful. Please verify your email.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'fullname': user.fullname,
                'email_verified': user.email_verified
            },
            'token': token
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Error creating account'}), 500

@auth_api.route("/login", methods=["POST"])
def login():
    """POST /api/auth/login - Login user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    if not username_or_email or not password:
        return jsonify({'error': 'Username/email and password required'}), 400
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Login with Flask-Login for session-based auth
    login_user(user, remember=remember)
    
    # Generate JWT token
    token = generate_token(user.id)
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'fullname': user.fullname,
            'email_verified': user.email_verified,
            'is_verified': user.is_verified,
            'is_private': user.is_private
        },
        'token': token
    }), 200

@auth_api.route("/logout", methods=["POST"])
@api_login_required
def logout():
    """POST /api/auth/logout - Logout user"""
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_api.route("/forgot-password", methods=["POST"])
def forgot_password():
    """POST /api/auth/forgot-password - Request password reset"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    # Don't reveal if email exists for security
    if user:
        send_password_reset_email(user)
    
    return jsonify({
        'message': 'If an account exists with that email, a password reset link has been sent.'
    }), 200

@auth_api.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    """POST /api/auth/reset-password/<token> - Reset password with token"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    password = data.get('password', '')
    
    if not password or len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
        return jsonify({'error': 'Reset token has expired'}), 400
    
    try:
        user.password = generate_password_hash(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        return jsonify({'message': 'Password reset successful'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({'error': 'Error resetting password'}), 500

@auth_api.route("/verify-email/<token>", methods=["GET", "POST"])
def verify_email(token):
    """GET/POST /api/auth/verify-email/<token> - Verify email with token"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        return jsonify({'error': 'Invalid verification token'}), 400
    
    if user.email_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    try:
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
        
        return jsonify({'message': 'Email verified successfully'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({'error': 'Error verifying email'}), 500

@auth_api.route("/resend-verification", methods=["POST"])
@api_login_required
def resend_verification():
    """POST /api/auth/resend-verification - Resend verification email"""
    user_id = getattr(request, 'current_user_id', None)
    if not user_id:
        user = current_user
    else:
        user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.email_verified:
        return jsonify({'message': 'Email already verified'}), 200
    
    if not user.email_verification_token:
        user.email_verification_token = generate_verification_token()
        db.session.commit()
    
    send_verification_email(user)
    
    return jsonify({'message': 'Verification email sent'}), 200

@auth_api.route("/me", methods=["GET"])
@api_login_required
def get_current_user():
    """GET /api/auth/me - Get current authenticated user"""
    user_id = getattr(request, 'current_user_id', None)
    if not user_id:
        user = current_user
    else:
        user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'fullname': user.fullname,
        'bio': user.bio,
        'profile_picture': user.profile_picture,
        'email_verified': user.email_verified,
        'is_verified': user.is_verified,
        'is_private': user.is_private,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }), 200

