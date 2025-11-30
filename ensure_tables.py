#!/usr/bin/env python3
"""Ensure all database tables exist"""

from app import create_app
from app.extension import db

# Import all models to register them
from app.models.users import User
from app.models.posts import Post
from app.models.comments import Comment
from app.models.likes import Like
from app.models.bookmarks import Bookmark
from app.models.follows import Follow
from app.models.notifications import Notification
from app.models.conversations import Conversation
from app.models.messages import Message
from app.models.stories import Story
from app.models.story_views import StoryView
from app.models.blocked_users import BlockedUser

app = create_app()

with app.app_context():
    print("Creating all database tables...")
    try:
        db.create_all()
        print("✓ All tables created successfully")
        
        # Verify key tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'users', 'posts', 'comments', 'likes', 'bookmarks', 
            'follows', 'notifications', 'conversations', 'messages',
            'stories', 'story_views', 'blocked_users'
        ]
        
        missing = []
        for table in required_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} MISSING")
                missing.append(table)
        
        if missing:
            print(f"\n⚠ Missing tables: {', '.join(missing)}")
        else:
            print("\n✓ All required tables exist!")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

