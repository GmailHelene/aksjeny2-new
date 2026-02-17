#!/usr/bin/env python3
"""
Setup test data for favorites debugging
"""
import sqlite3
import os
from datetime import datetime

# Database file path
db_path = '/workspaces/aksjeny2/app.db'

def setup_test_data():
    print("Setting up test data for favorites debugging...")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Creating users table...")
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(120) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Check if favorites table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
        if not cursor.fetchone():
            print("Creating favorites table...")
            cursor.execute('''
                CREATE TABLE favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    name VARCHAR(200),
                    exchange VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
        
        # Check if test user exists
        cursor.execute("SELECT id FROM users WHERE username = 'testuser'")
        user_row = cursor.fetchone()
        
        if not user_row:
            print("Creating test user...")
            # Simple password hash for testing
            password_hash = "pbkdf2:sha256:600000$test$12345"
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                ('testuser', 'test@example.com', password_hash)
            )
            user_id = cursor.lastrowid
        else:
            user_id = user_row[0]
            
        print(f"Test user ID: {user_id}")
        
        # Check if test user has favorites
        cursor.execute("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,))
        favorites_count = cursor.fetchone()[0]
        
        if favorites_count == 0:
            print("Creating test favorites...")
            test_favorites = [
                (user_id, 'AAPL', 'Apple Inc.', 'NASDAQ'),
                (user_id, 'GOOGL', 'Alphabet Inc.', 'NASDAQ'),
                (user_id, 'NEL.OL', 'Nel ASA', 'Oslo Børs'),
                (user_id, 'TSLA', 'Tesla Inc.', 'NASDAQ')
            ]
            
            cursor.executemany(
                "INSERT INTO favorites (user_id, symbol, name, exchange) VALUES (?, ?, ?, ?)",
                test_favorites
            )
            print(f"Created {len(test_favorites)} test favorites")
        else:
            print(f"Test user already has {favorites_count} favorites")
        
        # Commit changes
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM favorites")
        total_favorites = cursor.fetchone()[0]
        
        cursor.execute("SELECT symbol, name FROM favorites WHERE user_id = ?", (user_id,))
        user_favorites = cursor.fetchall()
        
        print(f"\n=== DATA VERIFICATION ===")
        print(f"Total users: {users_count}")
        print(f"Total favorites: {total_favorites}")
        print(f"Test user favorites:")
        for symbol, name in user_favorites:
            print(f"  - {symbol}: {name}")
        
        print(f"\n✅ Test data setup complete!")
        print(f"You can now:")
        print(f"1. Visit http://localhost:5002/test-favorites to see debug info")
        print(f"2. Visit http://localhost:5002/admin/test-login/testuser to login as test user")
        print(f"3. Visit http://localhost:5002/profile to test favorites display")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    setup_test_data()
