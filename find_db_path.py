"""
find_db_path.py - Finds the correct database path and examines its structure
"""

import os
import sys
import glob
from pathlib import Path

def find_database_file():
    """Find the database file used by the application"""
    # Possible database file names
    possible_db_files = ['app.db', 'aksjeradar.db', 'data.db', 'site.db']
    
    # Search for database files in the current directory and subdirectories
    for db_name in possible_db_files:
        # Check current directory
        if os.path.exists(db_name):
            print(f"✅ Found database file in current directory: {os.path.abspath(db_name)}")
            return os.path.abspath(db_name)
        
        # Check app directory
        app_path = os.path.join(os.path.dirname(__file__), 'app', db_name)
        if os.path.exists(app_path):
            print(f"✅ Found database file in app directory: {app_path}")
            return app_path
    
    # Search for .db files in the current directory and subdirectories
    print("🔍 Searching for database files...")
    db_files = []
    
    # Search in current directory
    db_files.extend(glob.glob('*.db'))
    
    # Search in app directory
    app_dir = os.path.join(os.path.dirname(__file__), 'app')
    if os.path.exists(app_dir):
        db_files.extend([os.path.join(app_dir, f) for f in glob.glob(os.path.join(app_dir, '*.db'))])
    
    # Search in instance directory
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    if os.path.exists(instance_dir):
        db_files.extend([os.path.join(instance_dir, f) for f in glob.glob(os.path.join(instance_dir, '*.db'))])
    
    if db_files:
        print(f"Found {len(db_files)} database files:")
        for i, db_file in enumerate(db_files):
            print(f"{i+1}. {db_file}")
        return db_files[0]  # Return the first one
    
    print("❌ No database files found!")
    return None

def examine_database(db_path):
    """Examine the database structure"""
    if not db_path or not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return
    
    try:
        import sqlite3
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n===== DATABASE STRUCTURE: {db_path} =====")
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables:")
        for i, (table_name,) in enumerate(tables):
            print(f"{i+1}. {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"   Columns ({len(columns)}):")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                print(f"     - {col_name} ({col_type}){' [PK]' if is_pk else ''}")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"   Rows: {row_count}")
            
            # If this is the users table, show some info
            if table_name == 'users' and row_count > 0:
                print("\n===== USERS TABLE DETAILS =====")
                
                # Check if test users exist
                test_emails = ['test@aksjeradar.trade', 'investor@aksjeradar.trade']
                for email in test_emails:
                    cursor.execute("SELECT id, username, email, password_hash, has_subscription, subscription_type, is_admin FROM users WHERE email = ?", (email,))
                    user = cursor.fetchone()
                    
                    if user:
                        user_id, username, user_email, pwd_hash, has_sub, sub_type, is_admin = user
                        print(f"\nUser: {user_email}")
                        print(f"  - ID: {user_id}")
                        print(f"  - Username: {username}")
                        print(f"  - Has password hash: {'Yes' if pwd_hash else 'No'}")
                        print(f"  - Password hash (first 20 chars): {pwd_hash[:20] + '...' if pwd_hash else 'None'}")
                        print(f"  - Has subscription: {'Yes' if has_sub else 'No'}")
                        print(f"  - Subscription type: {sub_type}")
                        print(f"  - Is admin: {'Yes' if is_admin else 'No'}")
                    else:
                        print(f"\nUser not found: {email}")
    
    except Exception as e:
        print(f"❌ Error examining database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connection
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Find database file
    db_path = find_database_file()
    
    if db_path:
        # Examine database
        examine_database(db_path)
    else:
        print("❌ Could not find database file!")
        sys.exit(1)
