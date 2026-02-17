"""
Flask application cache clearing script.
This script specifically targets Flask caching mechanisms.
"""
import os
import sys
from flask import Flask

# Create a minimal Flask app to access caching mechanisms
app = Flask(__name__)

# Try to clear Flask-Caching if it's being used
try:
    from flask_caching import Cache
    cache_config = {
        'CACHE_TYPE': 'SimpleCache',  # Use same type as in your app
    }
    cache = Cache(app, config=cache_config)
    cache.clear()
    print("✓ Flask-Caching cache cleared")
except ImportError:
    print("Flask-Caching not installed, skipping")
except Exception as e:
    print(f"✗ Error clearing Flask-Caching: {e}")

# Try to clear session files if using filesystem sessions
try:
    session_path = os.path.join('instance', 'sessions')
    if os.path.exists(session_path):
        session_files = os.listdir(session_path)
        for file in session_files:
            if file.endswith('.session'):
                os.remove(os.path.join(session_path, file))
        print(f"✓ Cleared {len(session_files)} session files")
except Exception as e:
    print(f"✗ Error clearing session files: {e}")

print("Flask application cache clearing completed!")
