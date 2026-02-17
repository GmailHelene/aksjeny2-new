#!/usr/bin/env python3
"""Force downgrade of any Eirik accounts to free (remove premium subscription)."""
from app import create_app
from app.models.user import User
from app.extensions import db
import os
from datetime import datetime

def run():
    os.environ['RAILWAY_ENVIRONMENT'] = '1'
    app = create_app('development')
    with app.app_context():
        targets = User.query.filter(User.email.ilike('%eirik%')).all()
        if not targets:
            print('No Eirik users found.')
            return
        for u in targets:
            print(f"Downgrading user id={u.id} email={u.email}")
            u.has_subscription = False
            u.subscription_type = 'free'
            u.subscription_end = datetime.utcnow()
        db.session.commit()
        print('Downgrade complete.')

if __name__ == '__main__':
    run()
