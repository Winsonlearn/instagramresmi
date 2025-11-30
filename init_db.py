#!/usr/bin/env python3
"""Initialize database for Instagram Clone"""

from app import create_app
from app.extension import db
from app.models.users import User
from app.models.posts import Post
from app.models.comments import Comment
from app.models.likes import Like
from app.models.follows import Follow
from app.models.bookmarks import Bookmark
from app.models.notifications import Notification

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("✓ Database tables created successfully!")
    print("✓ You can now run the application with: uv run python main.py")

