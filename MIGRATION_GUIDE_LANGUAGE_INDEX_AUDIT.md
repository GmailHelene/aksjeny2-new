# Migration Guide: preferred_language column & composite index

This guide covers applying the database changes introduced:
1. New column `preferred_language` on `users` table (nullable, default 'no').
2. Composite index `ix_portfolio_stocks_portfolio_deleted` on `portfolio_stocks(portfolio_id, deleted_at)`.

## Alembic Revision (example)
If using Alembic, create a new revision:
```
alembic revision -m "add preferred_language & composite index"
```
Then edit the generated file:
```python
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_pref_lang_composite_idx'
down_revision = '<PUT_PREVIOUS_REVISION_ID>'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add preferred_language column (nullable first for safe deploy)
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('preferred_language', sa.String(length=10), nullable=True))
        batch_op.create_index('ix_users_preferred_language', ['preferred_language'])
    # 2. Backfill (optional) - set to 'no' where NULL
    op.execute("UPDATE users SET preferred_language='no' WHERE preferred_language IS NULL")
    # 3. (Optional) enforce non-null if desired
    # with op.batch_alter_table('users') as batch_op:
    #     batch_op.alter_column('preferred_language', existing_type=sa.String(length=10), nullable=False)

    # 4. Composite index on portfolio_stocks
    op.create_index('ix_portfolio_stocks_portfolio_deleted', 'portfolio_stocks', ['portfolio_id','deleted_at'])


def downgrade():
    # Drop composite index
    op.drop_index('ix_portfolio_stocks_portfolio_deleted', table_name='portfolio_stocks')
    # Drop preferred_language idx & column
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_preferred_language')
        batch_op.drop_column('preferred_language')
```

## Raw SQL (PostgreSQL)
```sql
-- 1. Add column (if not exists guards for repeatability)
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10);
CREATE INDEX IF NOT EXISTS ix_users_preferred_language ON users(preferred_language);
UPDATE users SET preferred_language='no' WHERE preferred_language IS NULL;
-- 2. Composite index
CREATE INDEX IF NOT EXISTS ix_portfolio_stocks_portfolio_deleted ON portfolio_stocks(portfolio_id, deleted_at);
```

## Raw SQL (SQLite)
SQLite has limited ALTER abilities; adding a column works, but index creation is the same.
```sql
ALTER TABLE users ADD COLUMN preferred_language VARCHAR(10);
CREATE INDEX IF NOT EXISTS ix_users_preferred_language ON users(preferred_language);
UPDATE users SET preferred_language='no' WHERE preferred_language IS NULL;
CREATE INDEX IF NOT EXISTS ix_portfolio_stocks_portfolio_deleted ON portfolio_stocks(portfolio_id, deleted_at);
```
(If the column already exists, SQLite will error—ignore in dev or wrap in application logic.)

## Deployment Order (Zero / Minimal Downtime)
1. Deploy code that is backward compatible (models define new column, but application tolerates column missing) OR first apply schema then deploy code.
2. Apply migrations / SQL above.
3. Verify: SELECT preferred_language FROM users LIMIT 1; and .schema for index presence.
4. After traffic confirms, optionally enforce NOT NULL if business rule requires.

## Verification Queries
```sql
-- Check column
PRAGMA table_info(users); -- SQLite
\d users; -- Postgres

-- Index usage example (Postgres)
EXPLAIN ANALYZE SELECT * FROM portfolio_stocks WHERE portfolio_id=123 AND deleted_at IS NULL;
```
Look for index scan referencing ix_portfolio_stocks_portfolio_deleted.

## Rollback Strategy
If issues arise:
1. Revert application deploy (old code does not depend on new column).
2. (Optional) Drop index & column using downgrade or raw SQL:
```sql
DROP INDEX IF EXISTS ix_portfolio_stocks_portfolio_deleted; -- Postgres
DROP INDEX IF EXISTS ix_users_preferred_language; -- Postgres
ALTER TABLE users DROP COLUMN IF EXISTS preferred_language; -- Postgres
```
For SQLite, dropping column requires table rebuild; usually leave column in place instead of rollback.

## Notes
- Column kept nullable for compatibility; application handles missing by defaulting to 'no'.
- Composite index significantly speeds queries filtering active (deleted_at NULL) stocks per portfolio.
- Ensure no long-running transactions during index creation in production (Postgres supports CONCURRENTLY if needed):
```sql
CREATE INDEX CONCURRENTLY ix_portfolio_stocks_portfolio_deleted ON portfolio_stocks(portfolio_id, deleted_at);
```
Adjust Alembic script accordingly if using CONCURRENTLY (requires op.execute and manual management).

## Additional Optional Hardening
- Add CHECK constraint to restrict preferred_language to ('en','no').
```sql
ALTER TABLE users ADD CONSTRAINT chk_users_preferred_language CHECK (preferred_language IN ('en','no'));
```
- Add partial index for active stocks only (Postgres):
```sql
CREATE INDEX IF NOT EXISTS ix_portfolio_stocks_active ON portfolio_stocks(portfolio_id) WHERE deleted_at IS NULL;
```
This can outperform composite index for active-only lookups; keep whichever benchmarks better.

-- End of Guide
