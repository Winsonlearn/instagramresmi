from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extension import db
from app.forms.loginForm import LoginForm
from app.forms.signupForm import SignupForm
from app.forms.passwordResetForm import ForgotPasswordForm, ResetPasswordForm
from app.models.users import User
from app.models.user_settings import UserSettings
from app.lib.auth import generate_verification_token
from app.lib.email import send_verification_email, send_password_reset_email
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username_or_email = form.username.data.strip()
        
        # Try username first, then email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email.lower())
        ).first()
        
        if user:
            # Check password
            if check_password_hash(user.password, form.password.data):
                # Handle NULL is_active for old users
                if user.is_active is None:
                    user.is_active = True
                    db.session.commit()
                
                if not user.is_active:
                    flash('Account is deactivated. Please contact support.', 'error')
                else:
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    # Security: Validate next_page URL to prevent open redirect
                    if next_page and not next_page.startswith('/'):
                        next_page = None
                    return redirect(next_page) if next_page else redirect(url_for('main.feed'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User not found. Please check your username/email.', 'error')
    
    return render_template("auth/login.html", form=form)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))
    
    form = SignupForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data.strip()).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template("auth/signup.html", form=form)
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing_email:
            flash('Email already registered. Please use a different email or log in.', 'error')
            return render_template("auth/signup.html", form=form)
        
        # Create user with email verification token
        verification_token = generate_verification_token()
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            fullname=form.fullname.data.strip(),
            password=generate_password_hash(form.password.data),
            email_verification_token=verification_token,
            email_verified=False,
            is_private=False,
            is_active=True
        )
        
        try:
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create default user settings
            settings = UserSettings(user_id=user.id)
            db.session.add(settings)
            
            db.session.commit()
            
            # Send verification email
            send_verification_email(user)
            
            flash('Account created successfully! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
    
    return render_template("auth/signup.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Handle forgot password form"""
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        
        # Don't reveal if email exists (security)
        if user:
            send_password_reset_email(user)
        
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template("auth/forgot_password.html", form=form)

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))
    
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
        flash('Reset token has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.password = generate_password_hash(form.password.data)
            user.password_reset_token = None
            user.password_reset_expires = None
            db.session.commit()
            
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('Error resetting password. Please try again.', 'error')
    
    return render_template("auth/reset_password.html", form=form, token=token)

@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    """Verify email with token"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid verification token.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('main.feed'))
    
    try:
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
        
        flash('Email verified successfully!', 'success')
        return redirect(url_for('main.feed'))
    except Exception:
        db.session.rollback()
        flash('Error verifying email. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route("/resend-verification")
@login_required
def resend_verification():
    """Resend verification email"""
    if current_user.email_verified:
        flash('Email already verified.', 'info')
        return redirect(url_for('main.feed'))
    
    if not current_user.email_verification_token:
        current_user.email_verification_token = generate_verification_token()
        db.session.commit()
    
    send_verification_email(current_user)
    flash('Verification email sent. Please check your inbox.', 'info')
    return redirect(url_for('main.feed'))
