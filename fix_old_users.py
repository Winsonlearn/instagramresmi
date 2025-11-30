#!/usr/bin/env python3
"""Fix old users in database - set default values for new columns"""

from app import create_app
from app.extension import db
from app.models.users import User

app = create_app()

with app.app_context():
    print("Updating old users in database...")
    
    users = User.query.all()
    updated_count = 0
    
    for user in users:
        updated = False
        
        # Set default values for NULL columns
        if user.email_verified is None:
            user.email_verified = False
            updated = True
        
        if user.is_verified is None:
            user.is_verified = False
            updated = True
        
        if user.is_private is None:
            user.is_private = False
            updated = True
        
        if user.is_active is None:
            user.is_active = True  # Activate old users by default
            updated = True
        
        if updated:
            updated_count += 1
            print(f"  Updated user: {user.username}")
    
    if updated_count > 0:
        try:
            db.session.commit()
            print(f"\n✓ Updated {updated_count} user(s) successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error updating users: {e}")
    else:
        print("\n✓ No users need updating")
    
    # List all users
    print(f"\nUsers in database ({len(users)} total):")
    for user in users:
        print(f"  - {user.username} (email: {user.email or 'None'}, active: {user.is_active})")

