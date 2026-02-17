"""
direct_sqlite_fix.py - Direct SQLite fix for test user login issues
"""

import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

# Define output file for results
output_file = os.path.join(os.path.dirname(__file__), 'test_user_fix_results.txt')

def write_to_output(message):
    """Write a message to both console and output file"""
    print(message)
    with open(output_file, 'a') as f:
        f.write(message + '\n')

def clear_output_file():
    """Clear the output file"""
    with open(output_file, 'w') as f:
        f.write(f"Test User Fix Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")

def fix_test_users():
    """Fix test users using direct SQLite commands"""
    # Define database path
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    
    write_to_output(f"Looking for database at: {db_path}")
    
    if not os.path.exists(db_path):
        write_to_output(f"❌ Database not found at: {db_path}")
        return False
    
    write_to_output(f"✅ Database found: {db_path}")
    
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
        cursor = conn.cursor()
        
        write_to_output("Connected to database")
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            write_to_output("❌ Users table not found in database!")
            return False
        
        write_to_output("✅ Users table found")
        
        # Process each test user
        for user_data in test_users:
            email = user_data['email']
            username = user_data['username']
            password = user_data['password']
            
            # Generate password hash
            password_hash = generate_password_hash(password)
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user:
                user_id = user[0]
                write_to_output(f"\nUpdating existing user: {email} (ID: {user_id})")
                
                # Update user data with extra safety for null values
                update_query = """
                    UPDATE users SET 
                        username = ?,
                        password_hash = ?,
                        has_subscription = 1,
                        subscription_type = 'lifetime',
                        is_admin = 1
                    WHERE id = ?
                """
                cursor.execute(update_query, (username, password_hash, user_id))
                
                # Try to update date fields if they exist (might fail if schema is different)
                try:
                    cursor.execute(
                        "UPDATE users SET subscription_start = ? WHERE id = ?", 
                        (datetime.utcnow().isoformat(), user_id)
                    )
                except:
                    write_to_output("  - Note: Could not update subscription_start (field may not exist)")
                
                write_to_output(f"  - Updated username, password and subscription details")
            else:
                write_to_output(f"\nCreating new user: {email}")
                
                # Get column names to determine which fields we can insert
                cursor.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Basic columns that should always exist
                base_columns = ["username", "email", "password_hash"]
                base_values = [username, email, password_hash]
                
                # Additional columns that might exist
                additional_columns = {
                    "created_at": datetime.utcnow().isoformat(),
                    "has_subscription": 1,
                    "subscription_type": 'lifetime',
                    "subscription_start": datetime.utcnow().isoformat(),
                    "is_admin": 1,
                    "trial_used": 1
                }
                
                # Build the insert query dynamically based on available columns
                insert_columns = base_columns.copy()
                insert_values = base_values.copy()
                
                for col, val in additional_columns.items():
                    if col in columns:
                        insert_columns.append(col)
                        insert_values.append(val)
                
                # Create the INSERT statement
                placeholders = ", ".join(["?" for _ in insert_values])
                insert_query = f"""
                    INSERT INTO users ({", ".join(insert_columns)})
                    VALUES ({placeholders})
                """
                
                cursor.execute(insert_query, insert_values)
                write_to_output(f"  - Created new user with username {username}")
        
        # Commit changes
        conn.commit()
        write_to_output("\n✅ Changes committed to database")
        
        # Verify changes
        write_to_output("\n===== VERIFICATION =====")
        for user_data in test_users:
            email = user_data['email']
            cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user:
                user_id, db_username, db_email, pwd_hash = user
                write_to_output(f"\nUser: {db_email}")
                write_to_output(f"  - ID: {user_id}")
                write_to_output(f"  - Username: {db_username}")
                write_to_output(f"  - Has password hash: {'Yes' if pwd_hash else 'No'}")
                
                # Verify password
                from werkzeug.security import check_password_hash
                if check_password_hash(pwd_hash, user_data['password']):
                    write_to_output(f"  - ✅ Password verification successful!")
                else:
                    write_to_output(f"  - ❌ Password verification failed!")
            else:
                write_to_output(f"\nUser not found: {email} - Something went wrong!")
        
        return True
    
    except Exception as e:
        write_to_output(f"❌ Error fixing test users: {str(e)}")
        import traceback
        write_to_output(traceback.format_exc())
        return False
    
    finally:
        # Close connection
        if 'conn' in locals():
            conn.close()
            write_to_output("\nDatabase connection closed")

if __name__ == "__main__":
    # Clear output file
    clear_output_file()
    
    write_to_output("===== DIRECT SQLITE FIX FOR TEST USERS =====\n")
    
    # Fix test users
    success = fix_test_users()
    
    if success:
        write_to_output("\n✅ TEST USER FIX COMPLETED SUCCESSFULLY!")
        write_to_output("\nTest User Credentials:")
        write_to_output("1. Email: test@aksjeradar.trade")
        write_to_output("   Username: testuser")
        write_to_output("   Password: aksjeradar2024")
        write_to_output("\n2. Email: investor@aksjeradar.trade")
        write_to_output("   Username: investor")
        write_to_output("   Password: aksjeradar2024")
        write_to_output("\nPlease restart the Flask server before trying to login again.")
    else:
        write_to_output("\n❌ TEST USER FIX FAILED!")
        
    write_to_output(f"\n\nCheck the results file at: {output_file}")
