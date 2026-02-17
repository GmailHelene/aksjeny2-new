"""
force_create_test_users.py - Force create test users using a direct SQLite approach
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

# Configuration
DB_FILE = 'app.db'
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

# Connect to database
print(f"Opening database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Verify users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if not cursor.fetchone():
    print("ERROR: users table not found!")
    conn.close()
    exit(1)

# Delete existing test users
for user in TEST_USERS:
    cursor.execute("DELETE FROM users WHERE email = ?", (user['email'],))
    rows = cursor.rowcount
    print(f"Deleted {rows} existing records for {user['email']}")

# Insert new test users
for user in TEST_USERS:
    password_hash = generate_password_hash(user['password'])
    cursor.execute("""
    INSERT INTO users (
        username, 
        email, 
        password_hash, 
        has_subscription, 
        subscription_type, 
        is_admin,
        email_verified,
        trial_used
    ) VALUES (?, ?, ?, 1, 'lifetime', 1, 1, 1)
    """, (user['username'], user['email'], password_hash))
    
    new_id = cursor.lastrowid
    print(f"Created {user['email']} with ID {new_id}")

# Commit changes
conn.commit()
print("Changes committed")

# Verify users were created
print("\nVerifying users:")
for user in TEST_USERS:
    cursor.execute("SELECT id, username FROM users WHERE email = ?", (user['email'],))
    result = cursor.fetchone()
    if result:
        print(f"✓ {user['email']} exists with ID {result[0]}")
    else:
        print(f"✗ {user['email']} NOT FOUND")

# Close connection
conn.close()
print("\nDatabase connection closed")

print("\nTest user credentials:")
for user in TEST_USERS:
    print(f"Email: {user['email']}")
    print(f"Username: {user['username']}")
    print(f"Password: {user['password']}")
    print()

print("Please restart the Flask server before trying to log in.")
