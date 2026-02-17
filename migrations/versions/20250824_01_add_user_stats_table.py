"""add user_stats table

Revision ID: 20250824_01
Revises: 769884445837
Create Date: 2025-08-24 04:45:12.123456

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250824_01'
down_revision = '20240827_add_browser_enabled_to_price_alerts'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'user_stats' in inspector.get_table_names():
        return
    op.create_table('user_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # Achievement tracking
        sa.Column('stocks_analyzed', sa.Integer(), default=0),
        sa.Column('portfolios_created', sa.Integer(), default=0),
        sa.Column('watchlists_created', sa.Integer(), default=0),
        sa.Column('alerts_created', sa.Integer(), default=0),
        sa.Column('logins_count', sa.Integer(), default=0),
        sa.Column('days_active', sa.Integer(), default=0),
        
        # Feature usage tracking
        sa.Column('sentiment_analyses', sa.Integer(), default=0),
        sa.Column('technical_analyses', sa.Integer(), default=0),
        sa.Column('buffett_analyses', sa.Integer(), default=0),
        sa.Column('screener_searches', sa.Integer(), default=0),
        sa.Column('portfolio_updates', sa.Integer(), default=0),
        sa.Column('alerts_triggered', sa.Integer(), default=0),
        
        # Activity timestamps
        sa.Column('first_login', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), default=sa.func.now()),
        sa.Column('last_analysis', sa.DateTime(), nullable=True),
        sa.Column('last_portfolio_update', sa.DateTime(), nullable=True),
        sa.Column('last_alert_created', sa.DateTime(), nullable=True),
        
        # Achievement flags
        sa.Column('completed_profile', sa.Boolean(), default=False),
        sa.Column('verified_email', sa.Boolean(), default=False),
        sa.Column('added_first_stock', sa.Boolean(), default=False),
        sa.Column('created_first_alert', sa.Boolean(), default=False),
        sa.Column('shared_first_analysis', sa.Boolean(), default=False),
        
        # Feature discovery
        sa.Column('used_sentiment', sa.Boolean(), default=False),
        sa.Column('used_technical', sa.Boolean(), default=False),
        sa.Column('used_buffett', sa.Boolean(), default=False),
        sa.Column('used_screener', sa.Boolean(), default=False),
        sa.Column('used_alerts', sa.Boolean(), default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        
        # Primary key and foreign key constraint
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        
        # Indexes
        sa.Index('ix_user_stats_user_id', 'user_id')
    )

def downgrade():
    # Drop user_stats table
    op.drop_table('user_stats')
