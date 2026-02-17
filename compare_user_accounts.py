"""
compare_user_accounts.py - Compare the working helene721 account with test accounts
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

# Database path
db_path = 'app.db'

print(f"Looking for database at: {db_path}")
if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    exit(1)

print(f"Database found at: {db_path}")

# Working account and test accounts
accounts = [
    {'email': 'helene721@gmail.com', 'status': 'WORKING'},
    {'email': 'test@aksjeradar.trade', 'status': 'TEST'},
    {'email': 'investor@aksjeradar.trade', 'status': 'TEST'}
]

# Connect to database
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # This allows accessing results by column name
cursor = conn.cursor()

print("\n--- USER ACCOUNT COMPARISON ---")

# Get columns from users table
cursor.execute("PRAGMA table_info(users)")
columns = [column['name'] for column in cursor.fetchall()]
print(f"Found {len(columns)} columns in users table")

# Get relevant user information
for account in accounts:
    email = account['email']
    status = account['status']
    
    print(f"\n{status} ACCOUNT: {email}")
    
    # Check if user exists
    cursor.execute("""
        SELECT id, username, email, password_hash, has_subscription, subscription_type, 
               is_admin, email_verified, created_at
        FROM users 
        WHERE email = ?
    """, (email,))
    user = cursor.fetchone()
    
    if user:
        print(f"  ID: {user['id']}")
        print(f"  Username: {user['username']}")
        print(f"  Password hash exists: {'Yes' if user['password_hash'] else 'No'}")
        print(f"  Password hash prefix: {user['password_hash'][:20]}..." if user['password_hash'] else 'None')
        print(f"  Has subscription: {user['has_subscription']}")
        print(f"  Subscription type: {user['subscription_type']}")
        print(f"  Is admin: {user['is_admin']}")
        print(f"  Email verified: {user['email_verified']}")
        print(f"  Created at: {user['created_at']}")
    else:
        print(f"  ERROR: User not found in database!")

# Close connection
conn.close()
print("\nDatabase connection closed")

print("\nIf the working account has different values from the test accounts,")
print("run the clean_test_users.py script to update the test accounts.")
print("Then restart the Flask server with 'python main.py'.")
