from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    conn = db.engine.connect()
    try:
        conn.execute(text('ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10)'))
        print('Added preferred_language column')
    except Exception as e:
        print('preferred_language column add skipped:', e)
    try:
        conn.execute(text('CREATE INDEX IF NOT EXISTS ix_users_preferred_language ON users(preferred_language)'))
        print('Index created/exists for preferred_language')
    except Exception as e:
        print('Index creation skipped:', e)
    try:
        conn.execute(text('CREATE INDEX IF NOT EXISTS ix_portfolio_stocks_portfolio_deleted ON portfolio_stocks(portfolio_id, deleted_at)'))
        print('Composite index created/exists on portfolio_stocks')
    except Exception as e:
        print('Composite index creation skipped:', e)
    conn.close()
print('Migration bootstrap done')
