"""
Email utility functions for sending emails
"""
import os
from flask import url_for, current_app
from datetime import datetime, timedelta

def send_verification_email(user):
    """
    Send email verification email to user.
    In production, integrate with an email service like SendGrid, Mailgun, or AWS SES.
    For now, this is a placeholder that logs the verification link.
    """
    if not user.email:
        return False
    
    token = user.email_verification_token
    if not token:
        from app.lib.auth import generate_verification_token
        token = generate_verification_token()
        user.email_verification_token = token
        from app.extension import db
        db.session.commit()
    
    # In production, use actual email sending service
    # For development, print to console
    verification_url = url_for('auth_api.verify_email', token=token, _external=True)
    
    print(f"\n{'='*60}")
    print(f"EMAIL VERIFICATION (Development Mode)")
    print(f"To: {user.email}")
    print(f"Subject: Verify your email address")
    print(f"\nClick here to verify your email: {verification_url}")
    print(f"{'='*60}\n")
    
    # TODO: Replace with actual email sending
    # from flask_mail import Message
    # msg = Message(
    #     subject='Verify your email address',
    #     recipients=[user.email],
    #     html=f'<a href="{verification_url}">Click here to verify</a>'
    # )
    # mail.send(msg)
    
    return True

def send_password_reset_email(user):
    """
    Send password reset email to user.
    """
    if not user.email:
        return False
    
    from app.lib.auth import generate_reset_token
    from app.extension import db
    
    token = generate_reset_token()
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    reset_url = url_for('auth_api.reset_password', token=token, _external=True)
    
    print(f"\n{'='*60}")
    print(f"PASSWORD RESET EMAIL (Development Mode)")
    print(f"To: {user.email}")
    print(f"Subject: Reset your password")
    print(f"\nClick here to reset your password: {reset_url}")
    print(f"This link expires in 1 hour.")
    print(f"{'='*60}\n")
    
    # TODO: Replace with actual email sending
    # from flask_mail import Message
    # msg = Message(
    #     subject='Reset your password',
    #     recipients=[user.email],
    #     html=f'<a href="{reset_url}">Click here to reset your password</a>'
    # )
    # mail.send(msg)
    
    return True

