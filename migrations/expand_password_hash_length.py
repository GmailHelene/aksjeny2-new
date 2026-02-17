"""Idempotent migration to expand users.password_hash column length to 255.
Run manually: python migrations/expand_password_hash_length.py
"""
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()

SQLITE = 'sqlite' in str(db.engine.url.drivername)

ALTERS = [
    # Postgres / MySQL style
    "ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(255)",
    # SQLite needs table rebuild; we skip automatic for safety
]

def needs_change():
    insp = inspect(db.engine)
    for col in insp.get_columns('users'):
        if col['name'] == 'password_hash':
            type_repr = str(col['type']).lower()
            if '255' in type_repr:
                return False
            return True
    return False

with app.app_context():
    if not inspect(db.engine).has_table('users'):
        print('users table missing; nothing to do')
    elif not needs_change():
        print('password_hash already >= 255; no change needed')
    else:
        if SQLITE:
            print('SQLite detected; manual table rebuild required to alter column length. Skipping automated change.')
        else:
            for stmt in ALTERS:
                try:
                    with db.engine.begin() as conn:
                        conn.execute(text(stmt))
                    print('Applied:', stmt)
                    break
                except Exception as e:
                    print('Failed:', stmt, e)
            else:
                print('All ALTER attempts failed.')
