#!/usr/bin/env python3
"""
Block specific users from logging in and remove premium flags.
Run with: python3 block_users.py
"""
from app import create_app
from app.extensions import db
from app.models.user import User

BLOCK_EMAILS = [
    'eiriktollan.berntsen@gmail.com',
    'eirik@example.com',
]

def block_user(u: User):
    # Remove premium/admin flags; optional: mark a custom flag if exists
    changed = False
    if getattr(u, 'has_subscription', None):
        u.has_subscription = False
        changed = True
    if getattr(u, 'subscription_type', None):
        u.subscription_type = None
        changed = True
    if getattr(u, 'is_admin', None):
        u.is_admin = False
        changed = True
    # If model has an 'active' or 'is_active' flag, disable it
    for attr in ('active', 'is_active', 'enabled'):
        if hasattr(u, attr):
            try:
                setattr(u, attr, False)
                changed = True
            except Exception:
                pass
    return changed

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        for email in BLOCK_EMAILS:
            user = User.query.filter(User.email.ilike(email)).first()
            if not user:
                print(f"User {email}: NOT FOUND")
                continue
            changed = block_user(user)
            if changed:
                db.session.commit()
            print(f"User {email}: blocked login via auth layer; flags updated: {changed}")
