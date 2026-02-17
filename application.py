import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Railway production startup script
os.environ.setdefault('APP_ENV', 'production')
os.environ.setdefault('DATABASE_URL', 'sqlite:///app.db')
os.environ.setdefault('EMAIL_PORT', '587')
os.environ.setdefault('MAIL_SERVER', 'smtp.gmail.com')

print("Starting Flask app for Railway deployment...")

# Import app package here to avoid circular imports
from app import create_app

# Create the Flask app
app = create_app(os.getenv('APP_ENV', 'production'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=False, host='0.0.0.0', port=port)
else:
    # For Railway/WSGI deployment
    application = app
