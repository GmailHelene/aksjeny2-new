#!/usr/bin/env python3
from pathlib import Path
import os
from app import create_app
from app.models.user import User

lines = []

def log(s):
    print(s)
    lines.append(s)

if __name__ == '__main__':
    # Disable background services
    os.environ['RAILWAY_ENVIRONMENT'] = '1'
    os.environ['PORT'] = '1'
    app = create_app('development')
    with app.app_context():
        q = User.query.filter(User.email.ilike('%eirik%')).all()
        if not q:
            log('OK: No users matching eirik found')
        else:
            for u in q:
                log(f"FOUND: id={u.id} email={u.email} username={u.username} has_subscription={getattr(u,'has_subscription',None)} type={getattr(u,'subscription_type',None)} end={getattr(u,'subscription_end',None)} is_premium={getattr(u,'is_premium',None)}")
    Path('check_eirik_result.txt').write_text('\n'.join(lines), encoding='utf-8')
