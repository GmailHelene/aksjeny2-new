#!/usr/bin/env python3
"""
ensure_premium_user.py - Ensure a premium user exists for login testing

Creates or updates the user jarle@aksjeradar.trade with a valid password and
an active premium (lifetime) subscription so they can log in as a premium user.

Password (default): aksjeradar2024
"""
from __future__ import annotations

import sys
from datetime import datetime

try:
    from app import create_app
    from app.extensions import db
    from app.models.user import User
except Exception as e:
    print(f"❌ Failed to import app modules: {e}")
    sys.exit(2)


EMAIL = "jarle@aksjeradar.trade"
USERNAME = "jarle"
PASSWORD = "aksjeradar2024"


def ensure_user(email: str = EMAIL, username: str = USERNAME, password: str = PASSWORD) -> bool:
    app = create_app('development')
    with app.app_context():
        try:
            user = User.query.filter_by(email=email).first()
            created = False
            if not user:
                user = User(
                    email=email,
                    username=username,
                    has_subscription=True,
                    subscription_type='lifetime',
                    subscription_start=datetime.utcnow(),
                    email_verified=True,
                    is_admin=False,
                    trial_used=True,
                )
                try:
                    user.set_password(password)
                except Exception:
                    pass
                db.session.add(user)
                created = True
            else:
                # Upgrade existing user to premium and reset password
                user.has_subscription = True
                user.subscription_type = 'lifetime'
                if getattr(user, 'subscription_start', None) is None:
                    try:
                        user.subscription_start = datetime.utcnow()
                    except Exception:
                        pass
                user.email_verified = True
                user.trial_used = True
                try:
                    user.set_password(password)
                except Exception:
                    pass

            db.session.commit()

            # Output summary
            status = "created" if created else "updated"
            print(f"✅ Premium user {status}: {user.email}")
            print(f"   username: {user.username}")
            print(f"   has_subscription: {getattr(user, 'has_subscription', False)}")
            print(f"   subscription_type: {getattr(user, 'subscription_type', None)}")
            print(f"   email_verified: {getattr(user, 'email_verified', False)}")
            print(f"   is_admin: {getattr(user, 'is_admin', False)}")
            print("\nLogin credentials:")
            print(f"   Email:    {email}")
            print(f"   Password: {password}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to ensure premium user: {e}")
            return False


if __name__ == "__main__":
    ok = ensure_user()
    sys.exit(0 if ok else 1)
