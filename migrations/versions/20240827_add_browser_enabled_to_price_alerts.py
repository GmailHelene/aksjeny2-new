"""add browser_enabled column to price_alerts table

Revision ID: 20240827_add_browser_enabled_to_price_alerts
Create Date: 2024-08-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240827_add_browser_enabled_to_price_alerts'
down_revision = '46b5a3c74c95'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('price_alerts')]
    if 'browser_enabled' in cols:
        return
    op.add_column('price_alerts', sa.Column('browser_enabled', sa.Boolean(), nullable=False, server_default='0'))
    print("browser_enabled column added to price_alerts table successfully")

def downgrade():
    op.drop_column('price_alerts', 'browser_enabled')
    print("browser_enabled column dropped from price_alerts table")
