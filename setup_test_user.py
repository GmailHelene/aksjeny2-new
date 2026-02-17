#!/usr/bin/env python3
"""
Create a test user and simple login to test profile page
"""

from app import create_app
from app.models.user import User
from app.models.favorites import Favorites
from flask import session
import requests

app = create_app()

with app.app_context():
    # Check if test user exists
    test_user = User.query.filter_by(username='testuser').first()
    if not test_user:
        print("Creating test user...")
        from werkzeug.security import generate_password_hash
        
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpass123'),
            is_verified=True
        )
        from app import db
        db.session.add(test_user)
        db.session.commit()
        print(f"Created test user with ID: {test_user.id}")
    else:
        print(f"Test user exists with ID: {test_user.id}")
    
    # Add some test favorites for the test user
    existing_favs = Favorites.query.filter_by(user_id=test_user.id).count()
    if existing_favs == 0:
        print("Adding test favorites...")
        test_favorites = [
            Favorites(user_id=test_user.id, symbol='AAPL', name='Apple Inc.'),
            Favorites(user_id=test_user.id, symbol='TSLA', name='Tesla Inc.'),
            Favorites(user_id=test_user.id, symbol='GOOGL', name='Alphabet Inc.')
        ]
        
        from app import db
        for fav in test_favorites:
            db.session.add(fav)
        db.session.commit()
        print(f"Added {len(test_favorites)} test favorites")
    else:
        print(f"Test user already has {existing_favs} favorites")

print("\nTest user setup complete!")
print("Username: testuser")
print("Password: testpass123")
print("You can now login and test the profile page manually.")
