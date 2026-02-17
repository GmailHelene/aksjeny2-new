"""
direct_sqlite_user_fix.py - A direct fix that doesn't rely on SQLAlchemy or the Flask app
"""

import os
import sys
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# Test user credentials
TEST_USERS = [
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

# Find the database file
db_path = os.path.abspath('app.db')
print(f"Looking for database at: {db_path}")

if not os.path.exists(db_path):
    print(f"ERROR: Database not found at {db_path}")
    sys.exit(1)

print(f"Database found: {db_path}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("ERROR: Users table not found!")
        sys.exit(1)
    
    print("Users table found.")
    
    # Get all columns from the users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [column['name'] for column in cursor.fetchall()]
    print(f"Found {len(columns)} columns in users table.")
    
    # Process each test user
    for user in TEST_USERS:
        # Generate password hash
        password_hash = generate_password_hash(user['password'])
        
        print(f"\nFixing user: {user['email']}")
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user['email'],))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # Delete existing user to avoid conflicts
            cursor.execute("DELETE FROM users WHERE id = ?", (existing_user['id'],))
            print(f"Deleted existing user with ID {existing_user['id']}")
        
        # Common fields that should exist in all user tables
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # These are the basic fields we need
        values = {
            'username': user['username'],
            'email': user['email'],
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
        
        # Only include columns that exist in the table
        valid_columns = [col for col in values.keys() if col in columns]
        col_names = ', '.join(valid_columns)
        placeholders = ', '.join(['?' for _ in valid_columns])
        
        # Extract values in the same order as columns
        insert_values = [values[col] for col in valid_columns]
        
        # Insert new user
        cursor.execute(f"INSERT INTO users ({col_names}) VALUES ({placeholders})", insert_values)
        new_id = cursor.lastrowid
        print(f"Created new user with ID: {new_id}")
        
        # Verify the user was created correctly
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE id = ?", (new_id,))
        new_user = cursor.fetchone()
        
        if new_user:
            print(f"User created successfully:")
            print(f"  ID: {new_user['id']}")
            print(f"  Username: {new_user['username']}")
            print(f"  Email: {new_user['email']}")
            print(f"  Password hash present: {'Yes' if new_user['password_hash'] else 'No'}")
        else:
            print("ERROR: Failed to retrieve newly created user!")
    
    # Commit changes
    conn.commit()
    print("\nAll changes committed to database.")
    
    # Final verification
    print("\nFINAL VERIFICATION:")
    for user in TEST_USERS:
        cursor.execute("SELECT id, username, email FROM users WHERE email = ?", (user['email'],))
        result = cursor.fetchone()
        if result:
            print(f"✓ User {user['email']} verified with ID {result['id']}")
        else:
            print(f"✗ User {user['email']} NOT FOUND!")
    
    print("\nTEST USER CREDENTIALS:")
    for user in TEST_USERS:
        print(f"Email: {user['email']}")
        print(f"Username: {user['username']}")
        print(f"Password: {user['password']}")
        print()
    
    print("Please restart the Flask server before attempting to log in.")

except Exception as e:
    print(f"ERROR: {str(e)}")
    conn.rollback()
    raise

finally:
    if 'conn' in locals():
        conn.close()
        print("Database connection closed.")
