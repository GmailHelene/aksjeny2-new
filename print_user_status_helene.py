#!/usr/bin/env python3
from app import create_app
from app.models.user import User
from app.extensions import db

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        email = 'helene721@gmail.com'
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User {email}: NOT FOUND")
        else:
            print(f"User {email}: id={user.id}, admin={getattr(user,'is_admin',False)}, has_subscription={getattr(user,'has_subscription',False)}, type={getattr(user,'subscription_type',None)}")
