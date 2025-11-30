#!/usr/bin/env python3
"""Update database schema to match current models"""

from app import create_app
from app.extension import db
import sqlite3

app = create_app()

with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print(f"Updating database at: {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns in users table
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns if they don't exist
        columns_to_add = {
            'email_verified': 'BOOLEAN DEFAULT 0 NOT NULL',
            'is_verified': 'BOOLEAN DEFAULT 0 NOT NULL',
            'is_private': 'BOOLEAN DEFAULT 0 NOT NULL',
            'is_active': 'BOOLEAN DEFAULT 1 NOT NULL',
            'email_verification_token': 'VARCHAR(100)',
            'password_reset_token': 'VARCHAR(100)',
            'password_reset_expires': 'DATETIME',
            'last_login': 'DATETIME'
        }
        
        # Check follows table for status column
        cursor.execute("PRAGMA table_info(follows)")
        follows_columns = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in follows_columns:
            print("Adding status column to follows table...")
            try:
                cursor.execute("ALTER TABLE follows ADD COLUMN status VARCHAR(20) DEFAULT 'accepted' NOT NULL")
                conn.commit()
                print("✓ Added status column to follows table")
            except sqlite3.OperationalError as e:
                print(f"⚠ Could not add status to follows: {e}")
        
        # Check posts table for new columns
        cursor.execute("PRAGMA table_info(posts)")
        posts_columns = [row[1] for row in cursor.fetchall()]
        print(f"\nPosts table existing columns: {posts_columns}")
        
        posts_columns_to_add = {
            'media_urls': 'TEXT',
            'location': 'VARCHAR(255)'
        }
        
        # Migrate image_url to media_urls if needed
        if 'image_url' in posts_columns and 'media_urls' not in posts_columns:
            print("\nMigrating image_url to media_urls...")
            try:
                # Add media_urls column
                cursor.execute("ALTER TABLE posts ADD COLUMN media_urls TEXT")
                conn.commit()
                print("✓ Added media_urls column")
                
                # Migrate existing image_url data to media_urls (as JSON)
                import json
                cursor.execute("SELECT id, image_url FROM posts WHERE image_url IS NOT NULL")
                posts = cursor.fetchall()
                
                for post_id, image_url in posts:
                    if image_url:
                        # Convert old format to new JSON format
                        media_list = json.dumps([{"url": image_url, "type": "image", "alt_text": ""}])
                        cursor.execute("UPDATE posts SET media_urls = ? WHERE id = ?", (media_list, post_id))
                
                conn.commit()
                print(f"✓ Migrated {len(posts)} post(s) from image_url to media_urls")
            except Exception as e:
                print(f"⚠ Migration error: {e}")
                conn.rollback()
        
        # Add location column if missing
        if 'location' not in posts_columns:
            print("Adding location column to posts table...")
            try:
                cursor.execute("ALTER TABLE posts ADD COLUMN location VARCHAR(255)")
                conn.commit()
                print("✓ Added location column to posts table")
            except sqlite3.OperationalError as e:
                print(f"⚠ Could not add location: {e}")
        
        # Check comments table for parent_id column
        cursor.execute("PRAGMA table_info(comments)")
        comments_columns = [row[1] for row in cursor.fetchall()]
        print(f"\nComments table existing columns: {comments_columns}")
        
        if 'parent_id' not in comments_columns:
            print("Adding parent_id column to comments table...")
            try:
                cursor.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER")
                conn.commit()
                print("✓ Added parent_id column to comments table")
            except sqlite3.OperationalError as e:
                print(f"⚠ Could not add parent_id: {e}")
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                print(f"Adding column: {column_name}")
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    conn.commit()
                    print(f"✓ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠ Could not add {column_name}: {e}")
        
        print("\n✓ Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

