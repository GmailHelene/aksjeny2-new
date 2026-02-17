# Test User Login Fix Guide

## Problem
You've been having issues logging into the test accounts (`test@aksjeradar.trade` and `investor@aksjeradar.trade`) despite them being properly added to the exempt users list.

## Why This Is Happening
The login system requires:
1. User records to exist in the database
2. Passwords to be properly hashed using werkzeug.security
3. User subscription status to be correctly set

## Solution

We've created several scripts to fix the issue:

1. `force_create_test_users.py`: Most direct approach - deletes and recreates test users
2. `clean_test_users.py`: Updates existing users or creates new ones
3. `fixed_user_login.py`: More comprehensive approach with detailed logging
4. `one_step_fix.py`: Original fix script

## Fix Instructions

1. **Stop the Flask server** if it's running
2. **Run the fix script**:
   ```
   python force_create_test_users.py
   ```
3. **Restart the Flask server**:
   ```
   python main.py
   ```
4. **Log in with these credentials**:
   - Email: `test@aksjeradar.trade` / Password: `aksjeradar2024`
   - Email: `investor@aksjeradar.trade` / Password: `aksjeradar2024`

## Comparing with Working Account

The working account (`helene721@gmail.com`) has:
- A record in the users table
- A properly hashed password
- Correct subscription settings

Our fix scripts replicate this setup for the test accounts.

## If Problems Persist

1. Run `python compare_user_accounts.py` to see differences between accounts
2. Check for any error messages in the Flask server console when logging in
3. Try manually adding users through the Flask shell:
   ```python
   from app import create_app
   from app.models.user import User
   from app.extensions import db
   
   app = create_app()
   with app.app_context():
       user = User(
           username='testuser', 
           email='test@aksjeradar.trade',
           has_subscription=True,
           subscription_type='lifetime',
           is_admin=True
       )
       user.set_password('aksjeradar2024')
       db.session.add(user)
       db.session.commit()
   ```

## Important Notes

1. The exempt users list in `__init__.py` already includes these test users
2. The access control list already has these emails
3. The issue is likely related to the database records or password hashing

After running the fix script and restarting the server, the login should work just like the working account.
