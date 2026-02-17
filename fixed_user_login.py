"""
fixed_user_login.py - An improved fix for test user login issues
"""

import os
import sys
import sqlite3
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Create a log file
log_file = os.path.join(os.path.dirname(__file__), 'fixed_user_login_log.txt')

def log(message):
    """Log a message to both console and log file"""
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{message}\n")

# Initialize log file
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"Test User Fix Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 50 + "\n\n")

# Find the database file
db_path = os.path.join(os.path.dirname(__file__), 'app.db')
log(f"Looking for database at: {db_path}")

if not os.path.exists(db_path):
    log(f"❌ Database not found at: {db_path}")
    sys.exit(1)

log(f"✅ Database found: {db_path}")

# Test user data
test_users = [
    {
        'email': 'test@aksjeradar.trade',
        'username': 'testuser',
        'password': 'aksjeradar2024'
    },
    {
        'email': 'investor@aksjeradar.trade',
        'username': 'investor',
        'password': 'aksjeradar2024'
    }
]

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    cursor = conn.cursor()
    
    log("Connected to database")
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        log("❌ Users table not found in database!")
        sys.exit(1)
    
    log("✅ Users table found")
    
    # Get schema information for the users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [column['name'] for column in cursor.fetchall()]
    log(f"Found {len(columns)} columns in users table")
    
    # Process each test user
    for user_data in test_users:
        email = user_data['email']
        username = user_data['username']
        password = user_data['password']
        
        # Generate password hash
        password_hash = generate_password_hash(password)
        log(f"\nFixing user: {email}")
        log(f"- Generated password hash: {password_hash[:20]}...")
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            log(f"- User exists with ID: {user_id}")
            
            # Delete existing user (to avoid any schema issues)
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            log(f"- Deleted existing user record to recreate cleanly")
            
            # Create user from scratch
            now = datetime.utcnow()
            
            # Prepare insert values with defaults for any missing columns
            values = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'created_at': now,
                'has_subscription': 1,
                'subscription_type': 'lifetime',
                'subscription_start': now,
                'subscription_end': None,
                'trial_used': 1,
                'is_admin': 1,
                'email_verified': 1
            }
            
            # Build dynamic INSERT query based on existing columns
            valid_columns = [col for col in values.keys() if col in columns]
            placeholders = ', '.join(['?'] * len(valid_columns))
            col_names = ', '.join(valid_columns)
            
            # Extract values in the same order as columns
            insert_values = [values[col] for col in valid_columns]
            
            # Execute the INSERT
            cursor.execute(f"INSERT INTO users ({col_names}) VALUES ({placeholders})", insert_values)
            user_id = cursor.lastrowid
            log(f"- Created new user with ID: {user_id}")
        else:
            # Create new user from scratch
            now = datetime.utcnow()
            
            # Prepare insert values with defaults for any missing columns
            values = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'created_at': now,
                'has_subscription': 1,
                'subscription_type': 'lifetime',
                'subscription_start': now,
                'subscription_end': None,
                'trial_used': 1,
                'is_admin': 1,
                'email_verified': 1
            }
            
            # Build dynamic INSERT query based on existing columns
            valid_columns = [col for col in values.keys() if col in columns]
            placeholders = ', '.join(['?'] * len(valid_columns))
            col_names = ', '.join(valid_columns)
            
            # Extract values in the same order as columns
            insert_values = [values[col] for col in valid_columns]
            
            # Execute the INSERT
            cursor.execute(f"INSERT INTO users ({col_names}) VALUES ({placeholders})", insert_values)
            user_id = cursor.lastrowid
            log(f"- Created new user with ID: {user_id}")
    
    # Commit changes
    conn.commit()
    log("\n✅ Changes committed to database")
    
    # Verify changes
    log("\n===== VERIFICATION =====")
    for user_data in test_users:
        email = user_data['email']
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            db_username = user['username']
            db_email = user['email']
            pwd_hash = user['password_hash']
            
            log(f"\nUser: {db_email}")
            log(f"- ID: {user_id}")
            log(f"- Username: {db_username}")
            log(f"- Has password hash: {'Yes' if pwd_hash else 'No'}")
            
            # Test password verification
            from werkzeug.security import check_password_hash
            if check_password_hash(pwd_hash, user_data['password']):
                log(f"- ✅ Password verification successful")
            else:
                log(f"- ❌ Password verification failed")
        else:
            log(f"\n❌ User not found: {email} - Something went wrong!")
    
    log("\n✅ FIX COMPLETED SUCCESSFULLY")
    log("\nTest User Credentials:")
    log("1. Email: test@aksjeradar.trade")
    log("   Username: testuser")
    log("   Password: aksjeradar2024")
    log("\n2. Email: investor@aksjeradar.trade")
    log("   Username: investor")
    log("   Password: aksjeradar2024")
    log("\nPlease restart the Flask server before trying to login again.")
    
except Exception as e:
    log(f"\n❌ Error: {str(e)}")
    import traceback
    log(traceback.format_exc())
    sys.exit(1)
finally:
    # Close connection
    if 'conn' in locals():
        conn.close()
        log("\nDatabase connection closed")

log(f"\nLog file saved at: {log_file}")
log("Please check this file for detailed results of the fix operation.")
