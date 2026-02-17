#!/usr/bin/env python3
"""Idempotent migration: add deleted_at column to portfolio_stocks if absent.
Works for PostgreSQL or SQLite.
"""
from app import create_app, db
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError

app = create_app('development')

SQL_CHECK = """
SELECT column_name FROM information_schema.columns
WHERE table_name='portfolio_stocks' AND column_name='deleted_at';
"""

ALTER_PG = "ALTER TABLE portfolio_stocks ADD COLUMN deleted_at TIMESTAMP NULL;"
CREATE_INDEX = "CREATE INDEX IF NOT EXISTS ix_portfolio_stocks_portfolio_deleted ON portfolio_stocks (portfolio_id, deleted_at);"

with app.app_context():
    engine = db.engine
    dialect = engine.dialect.name
    try:
        has_col = False
        with engine.connect() as conn:
            if dialect == 'postgresql':
                res = conn.execute(text(SQL_CHECK))
                has_col = res.first() is not None
            elif dialect == 'sqlite':
                res = conn.execute(text("PRAGMA table_info(portfolio_stocks);"))
                cols = [r[1] for r in res.fetchall()]
                has_col = 'deleted_at' in cols
        if has_col:
            print("deleted_at already present; nothing to do.")
        else:
            print("Adding deleted_at column...")
            with engine.begin() as conn:
                conn.execute(text(ALTER_PG if dialect == 'postgresql' else "ALTER TABLE portfolio_stocks ADD COLUMN deleted_at DATETIME NULL"))
                try:
                    conn.execute(text(CREATE_INDEX))
                except Exception as idx_err:
                    print(f"Index creation warning: {idx_err}")
            print("Migration complete.")
    except (ProgrammingError, OperationalError) as e:
        print(f"Migration failed: {e}")
        raise SystemExit(1)
