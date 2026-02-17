#!/usr/bin/env python3
"""
Remove Eirik's user account and related data from the database.
"""
from pathlib import Path
import os
from app import create_app, db
from app.models.user import User

LOG = []

def log(msg: str):
    print(msg)
    LOG.append(msg)

TARGET_EMAILS = [
    'eiriktollan.berntsen@gmail.com',
    'eirik@aksjeradar.trade',
]

if __name__ == '__main__':
    # Disable background services to speed up app init
    os.environ['RAILWAY_ENVIRONMENT'] = '1'
    os.environ['PORT'] = '1'
    app = create_app('development')
    with app.app_context():
        removed = 0
        for email in TARGET_EMAILS:
            user = User.query.filter_by(email=email).first()
            if not user:
                log(f"Not found: {email}")
                continue
            try:
                uid = user.id
                uname = user.username
                db.session.delete(user)  # cascades portfolios/watchlists
                db.session.commit()
                removed += 1
                log(f"Deleted user id={uid} email={email} username={uname}")
            except Exception as e:
                db.session.rollback()
                log(f"ERROR deleting {email}: {e}")
        log(f"Total users removed: {removed}")
    Path('remove_eirik_result.txt').write_text("\n".join(LOG), encoding='utf-8')
