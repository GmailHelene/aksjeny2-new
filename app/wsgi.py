#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

try:
    from app import create_app
    
    # Create the application instance
    app = create_app('production')
    
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
        
except Exception as e:
    print(f"❌ Failed to create app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
