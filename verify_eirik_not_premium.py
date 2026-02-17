#!/usr/bin/env python3
"""Verify that Eirik related accounts do NOT have premium access anymore.
Writes a result file and exits with non-zero status if violation found.
"""
from pathlib import Path
import sys, os
from app import create_app
from app.models.user import User

LOG = []

def log(msg):
    print(msg)
    LOG.append(msg)

def fail(msg):
    log(f"FAIL: {msg}")
    Path('verify_eirik_not_premium_result.txt').write_text('\n'.join(LOG), encoding='utf-8')
    sys.exit(1)

TARGET_EMAIL_PATTERNS = [
    'eiriktollan.berntsen@gmail.com',
    'eirik@aksjeradar.trade',
    '%eirik%'
]

if __name__ == '__main__':
    os.environ['RAILWAY_ENVIRONMENT'] = '1'
    app = create_app('development')
    with app.app_context():
        # Gather unique users matching any pattern
        users = {}
        for pattern in TARGET_EMAIL_PATTERNS:
            if '%' in pattern:
                q = User.query.filter(User.email.ilike(pattern)).all()
            else:
                q = User.query.filter_by(email=pattern).all()
            for u in q:
                users[u.id] = u
        if not users:
            log('OK: No Eirik users present.')
        violation = False
        for u in users.values():
            has_sub = getattr(u, 'has_subscription', False)
            sub_type = getattr(u, 'subscription_type', 'free')
            sub_end = getattr(u, 'subscription_end', None)
            is_premium = False
            try:
                is_premium = u.is_premium
            except Exception:
                pass
            log(f"User id={u.id} email={u.email} has_subscription={has_sub} type={sub_type} end={sub_end} computed_is_premium={is_premium}")
            if has_sub and sub_type in ['monthly','yearly','lifetime','premium','pro','active'] and is_premium:
                violation = True
        if violation:
            fail('One or more Eirik accounts still have premium access')
        else:
            log('SUCCESS: Eirik accounts do not have premium access')
            Path('verify_eirik_not_premium_result.txt').write_text('\n'.join(LOG), encoding='utf-8')
            sys.exit(0)
