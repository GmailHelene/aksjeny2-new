#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Select environment: APP_ENV preferred, fallback to FLASK_ENV then production
if not os.environ.get('APP_ENV') and not os.environ.get('FLASK_ENV'):
    os.environ.setdefault('APP_ENV', 'production')

try:
    # Import after environment variables are set
    from app import create_app
    
    # Determine env name
    env_name = os.environ.get('APP_ENV') or os.environ.get('FLASK_ENV') or 'production'
    app = create_app(env_name)
    
    # Ensure app is ready
    with app.app_context():
        from app.extensions import db
        # Create tables if they don't exist
        try:
            db.create_all()
            print("✅ Database tables initialized")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
    
    print(f"✅ WSGI app initialized successfully (env={env_name})")

except Exception as e:
    print(f"❌ WSGI app initialization failed: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export for gunicorn
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
