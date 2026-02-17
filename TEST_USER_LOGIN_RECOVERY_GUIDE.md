# Test User Login Recovery Guide

## Problem
You're having trouble logging in with the test user accounts:
- Email: `test@aksjeradar.trade`
- Email: `investor@aksjeradar.trade`
- Password: `aksjeradar2024`

## Solutions

We've created several scripts to fix this issue. Please try the following steps in order:

### 1. Stop the Flask Server
First, stop any running Flask server by pressing `Ctrl+C` in the terminal where it's running.

### 2. Run the Comprehensive Fix Script
Run the following command in your terminal:
```
python comprehensive_test_user_fix.py
```

### 3. Run the Direct SQLite Fix
If the first script didn't work, try the direct SQLite fix:
```
python direct_sqlite_fix.py
```

### 4. Run the Flask App User Fix
If the previous scripts didn't work, try the Flask app user fix:
```
python flask_app_user_fix.py
```

### 5. Manually Update the Database

If none of the scripts worked, you can manually update the database using SQLite:

1. Open the SQLite database:
   ```
   sqlite3 app.db
   ```

2. Check if the users exist:
   ```sql
   SELECT id, username, email, password_hash FROM users WHERE email IN ('test@aksjeradar.trade', 'investor@aksjeradar.trade');
   ```

3. If they exist, update their passwords:
   ```sql
   UPDATE users 
   SET password_hash = '$2b$12$QEDl0nxSIkFSFJkwmhOz4.jWlb47wDsWb0jQTMTbp2IkrxNRJlQq6', 
       has_subscription = 1, 
       subscription_type = 'lifetime', 
       is_admin = 1 
   WHERE email IN ('test@aksjeradar.trade', 'investor@aksjeradar.trade');
   ```

4. If they don't exist, create them:
   ```sql
   INSERT INTO users (username, email, password_hash, has_subscription, subscription_type, is_admin, created_at)
   VALUES 
       ('testuser', 'test@aksjeradar.trade', '$2b$12$QEDl0nxSIkFSFJkwmhOz4.jWlb47wDsWb0jQTMTbp2IkrxNRJlQq6', 1, 'lifetime', 1, CURRENT_TIMESTAMP),
       ('investor', 'investor@aksjeradar.trade', '$2b$12$QEDl0nxSIkFSFJkwmhOz4.jWlb47wDsWb0jQTMTbp2IkrxNRJlQq6', 1, 'lifetime', 1, CURRENT_TIMESTAMP);
   ```

### 6. Restart the Flask Server
After applying any of these fixes, restart the Flask server:
```
python main.py
```

## Explanation of the Issue

The login issue is likely caused by one of the following:

1. **Invalid Password Hash**: The password hash stored in the database may be incorrect or using a different hashing algorithm than expected.

2. **Missing User Records**: The test user accounts might not exist in the database.

3. **Database Schema Issues**: The database schema might not match the expected structure in the User model.

4. **Authentication Logic Issues**: There might be issues in the login logic that prevent successful authentication.

The scripts provided attempt to fix these issues by:
- Creating the users if they don't exist
- Updating the password hashes using Werkzeug's generate_password_hash function
- Setting the premium subscription status to ensure access
- Setting the admin status to ensure full access

## Credentials to Use
Once fixed, you should be able to log in with:

### Test User
- Email: `test@aksjeradar.trade`
- Username: `testuser`
- Password: `aksjeradar2024`

### Investor Test User
- Email: `investor@aksjeradar.trade`
- Username: `investor`
- Password: `aksjeradar2024`

These users should have full admin access and lifetime premium subscriptions.
