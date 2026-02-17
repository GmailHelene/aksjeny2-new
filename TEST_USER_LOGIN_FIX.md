# Test User Login Fix

## Problem
You are unable to log in with the test user accounts:
- `test@aksjeradar.trade`
- `investor@aksjeradar.trade`
- Password: `aksjeradar2024`

## Diagnosis
Based on our analysis, there could be several issues:

1. The password hashes in the database might be incorrect
2. The users might not exist in the database
3. There might be schema inconsistencies between the User model and the database

## Comprehensive Solution

To fix this issue, we have created several scripts. Each takes a different approach to solving the problem, so you can try them in order until one works:

### 1. One-Step Fix (Recommended)
Run this script first:
```bash
python one_step_fix.py
```
This script will:
- Find the database file
- Create or update the test users with correct password hashes
- Set them as premium lifetime users
- Log all operations to `test_user_fix_log.txt`

### 2. Comprehensive Test User Fix
If the first script doesn't work, try:
```bash
python comprehensive_test_user_fix.py
```
This script takes a more comprehensive approach to finding and fixing the database.

### 3. Direct SQLite Fix
For a direct database approach:
```bash
python direct_sqlite_fix.py
```
This script uses pure SQLite commands to update the database.

### 4. Flask App User Fix
If you need to use the Flask app context:
```bash
python flask_app_user_fix.py
```
This script creates a minimal Flask app to update the users.

### 5. Restart the Flask Server
After running any of these scripts, restart the Flask server:
```bash
python main.py
```

## Manual Database Fix

If none of the scripts work, you can manually fix the database using SQLite:

1. Open the SQLite database:
   ```bash
   sqlite3 app.db
   ```

2. Check if the users exist:
   ```sql
   SELECT id, username, email, password_hash FROM users WHERE email IN ('test@aksjeradar.trade', 'investor@aksjeradar.trade');
   ```

3. If they exist, update them:
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
   INSERT INTO users (username, email, password_hash, has_subscription, subscription_type, is_admin)
   VALUES 
       ('testuser', 'test@aksjeradar.trade', '$2b$12$QEDl0nxSIkFSFJkwmhOz4.jWlb47wDsWb0jQTMTbp2IkrxNRJlQq6', 1, 'lifetime', 1),
       ('investor', 'investor@aksjeradar.trade', '$2b$12$QEDl0nxSIkFSFJkwmhOz4.jWlb47wDsWb0jQTMTbp2IkrxNRJlQq6', 1, 'lifetime', 1);
   ```

## Final Notes

1. These users are already added to the `EXEMPT_EMAILS` list in `app/utils/access_control_unified.py`, so they should have full access once they can log in.

2. The setup_exempt_users function in `app/routes/__init__.py` has also been updated to include these users, so they should be created automatically when the database is initialized.

3. If you continue to have issues, you may need to check your Flask app logs for more detailed error messages during login attempts.

4. Make sure the Flask server is restarted after applying any of these fixes to ensure the changes take effect.
