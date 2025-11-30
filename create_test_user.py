#!/usr/bin/env python3
"""Create a test user for login testing"""

from app import create_app
from app.extension import db
from app.models.users import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    username = 'ayamobaaaa'
    password = 'ayamobaaaa'  # Same as username for testing
    
    # Check if user exists
    existing_user = User.query.filter_by(username=username).first()
    
    if existing_user:
        print(f"User '{username}' already exists!")
        print(f"To reset password, use the forgot password feature.")
    else:
        # Create new user
        user = User(
            username=username,
            email=f'{username}@example.com',  # Temporary email
            fullname=username.title(),
            password=generate_password_hash(password),
            email_verified=True,  # Auto-verify for testing
            is_active=True,
            is_private=False
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            print("=" * 60)
            print("✓ Test user created successfully!")
            print("=" * 60)
            print(f"Username: {username}")
            print(f"Password: {password}")
            print(f"Email: {user.email}")
            print("=" * 60)
            print("You can now login with these credentials.")
            print("=" * 60)
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating user: {e}")

