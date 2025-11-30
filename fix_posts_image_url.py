#!/usr/bin/env python3
"""Fix posts table image_url column to be nullable"""

from app import create_app
import sqlite3

app = create_app()

with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print(f"Fixing database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute('PRAGMA table_info(posts)')
        columns = cursor.fetchall()
        image_url_column = [col for col in columns if col[1] == 'image_url']
        
        if image_url_column:
            col = image_url_column[0]
            print(f"Current image_url column: nullable={not col[3]}")
            
            if col[3]:  # If NOT NULL
                print("Making image_url column nullable...")
                # SQLite doesn't support ALTER COLUMN directly, need to recreate table
                # But we can use a workaround by creating a new column and copying data
                
                # Check if column is NOT NULL
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'")
                create_sql = cursor.fetchone()[0]
                
                # If image_url is NOT NULL, we need to update existing NULL values first
                # Then we'll alter the column constraint (SQLite 3.31.0+ supports this)
                try:
                    # Try to alter column (newer SQLite versions)
                    cursor.execute("ALTER TABLE posts ALTER COLUMN image_url DROP NOT NULL")
                    conn.commit()
                    print("✓ Made image_url nullable using ALTER COLUMN")
                except sqlite3.OperationalError:
                    # Older SQLite versions - need to recreate table
                    print("Using workaround for older SQLite...")
                    
                    # First, set any NULL values to empty string for existing rows
                    cursor.execute("UPDATE posts SET image_url = '' WHERE image_url IS NULL")
                    
                    # For SQLite, we can't directly modify column constraints
                    # We'll need to ensure we don't insert NULL, but use empty string or handle in code
                    print("⚠ Note: SQLite doesn't support ALTER COLUMN DROP NOT NULL")
                    print("  Setting default empty string for NULL values")
        else:
            print("image_url column not found - checking media_urls...")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'")
            create_sql = cursor.fetchone()[0]
            print("Posts table SQL:", create_sql[:200] + "...")
        
        conn.close()
        print("✓ Database check complete")
    except Exception as e:
        conn.close()
        print(f"✗ Error: {e}")

