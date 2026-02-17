"""
Migration: unify notification preferences into user_notification_preferences table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_price_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_news_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_portfolio_updates', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_watchlist_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_weekly_reports', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_price_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_news_alerts', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('push_portfolio_updates', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('push_watchlist_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_weekly_reports', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('inapp_price_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('inapp_news_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('inapp_portfolio_updates', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('inapp_watchlist_alerts', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('inapp_weekly_reports', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('quiet_hours_start', sa.String(5), nullable=False, server_default='22:00'),
        sa.Column('quiet_hours_end', sa.String(5), nullable=False, server_default='08:00'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='Europe/Oslo'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

def downgrade():
    op.drop_table('user_notification_preferences')
