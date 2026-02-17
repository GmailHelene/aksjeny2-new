"""
direct_db_fix.py - Direct database fix for test user passwords
This script uses direct SQL to update the password hashes in the database.
"""

import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash

# Get database file path
db_path = os.path.join(os.path.dirname(__file__), 'app.db')

# Check if database file exists
if not os.path.exists(db_path):
    print(f"❌ Database file not found at: {db_path}")
    sys.exit(1)

# Test user credentials
test_users = [
    {
        'email': 'test@aksjeradar.trade',
        'password': 'aksjeradar2024'
    },
    {
        'email': 'investor@aksjeradar.trade',
        'password': 'aksjeradar2024'
    }
]

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"✅ Connected to database: {db_path}")
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("❌ Users table not found in database!")
        sys.exit(1)
    
    # Check existing test users
    for user in test_users:
        email = user['email']
        password = user['password']
        
        # Generate new password hash
        password_hash = generate_password_hash(password)
        
        # Check if user exists
        cursor.execute("SELECT id, username, password_hash FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        if result:
            user_id, username, current_hash = result
            print(f"\nFound user: {email} (ID: {user_id}, Username: {username})")
            
            # Update password hash
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            print(f"  - Updated password hash")
            
            # Update subscription status
            cursor.execute("""
                UPDATE users 
                SET has_subscription = 1, 
                    subscription_type = 'lifetime', 
                    is_admin = 1
                WHERE id = ?
            """, (user_id,))
            print(f"  - Updated subscription status (lifetime)")
        else:
            print(f"\nUser not found: {email}")
            print("  - Will not create new user with direct SQL for safety")
    
    # Commit changes
    conn.commit()
    print("\n✅ Changes committed to database")
    
    # Verify changes
    print("\n===== VERIFICATION =====")
    for user in test_users:
        email = user['email']
        cursor.execute("SELECT id, username, password_hash, has_subscription, subscription_type, is_admin FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        if result:
            user_id, username, pwd_hash, has_sub, sub_type, is_admin = result
            print(f"\nUser: {email}")
            print(f"  - ID: {user_id}")
            print(f"  - Username: {username}")
            print(f"  - Has password hash: {'Yes' if pwd_hash else 'No'}")
            print(f"  - Has subscription: {'Yes' if has_sub else 'No'}")
            print(f"  - Subscription type: {sub_type}")
            print(f"  - Is admin: {'Yes' if is_admin else 'No'}")
        else:
            print(f"\nUser still not found: {email}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Close connection
    if 'conn' in locals():
        conn.close()
        print("\n✅ Database connection closed")

print("\n🎉 Script completed! Please restart the Flask server before trying to login again.")
