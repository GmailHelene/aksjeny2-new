"""
clean_test_users.py - Clean script to fix test user login issues
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

# Test users to fix
test_users = [
    {'email': 'test@aksjeradar.trade', 'username': 'testuser', 'password': 'aksjeradar2024'},
    {'email': 'investor@aksjeradar.trade', 'username': 'investor', 'password': 'aksjeradar2024'}
]

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Connected to database")

for user in test_users:
    email = user['email']
    username = user['username']
    password = user['password']
    password_hash = generate_password_hash(password)
    
    print(f"\nProcessing user: {email}")
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        user_id = existing_user[0]
        print(f"User exists with ID: {user_id}")
        
        # Update password and subscription
        cursor.execute("""
            UPDATE users SET 
                password_hash = ?,
                has_subscription = 1,
                subscription_type = 'lifetime',
                is_admin = 1,
                email_verified = 1
            WHERE id = ?
        """, (password_hash, user_id))
        
        print(f"Updated user password and subscription details")
    else:
        print(f"User does not exist, creating new")
        
        # Insert new user with minimal fields
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, has_subscription, subscription_type, is_admin)
            VALUES (?, ?, ?, 1, 'lifetime', 1)
        """, (username, email, password_hash))
        
        new_id = cursor.lastrowid
        print(f"Created new user with ID: {new_id}")

# Commit changes
conn.commit()
print("\nChanges committed to database")

# Verify changes
print("\n--- VERIFICATION ---")
for user in test_users:
    email = user['email']
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    
    if result:
        print(f"User {email}:")
        print(f"  ID: {result[0]}")
        print(f"  Username: {result[1]}")
        print(f"  Password hash exists: {'Yes' if result[3] else 'No'}")
    else:
        print(f"ERROR: User {email} not found in database!")

# Close connection
conn.close()
print("\nDatabase connection closed")

print("\nTEST USER CREDENTIALS:")
for user in test_users:
    print(f"Email: {user['email']}")
    print(f"Username: {user['username']}")
    print(f"Password: {user['password']}")
    print()

print("Please restart the Flask server before attempting to log in.")
