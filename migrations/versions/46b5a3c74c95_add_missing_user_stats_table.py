"""add missing user_stats table migration

Revision ID: 46b5a3c74c95
Create Date: 2024-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '46b5a3c74c95'
down_revision = '769884445837'
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
        sa.Column('predictions_made', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_predictions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stocks_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('portfolios_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_logins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('consecutive_login_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_login_date', sa.Date(), nullable=True),
        sa.Column('forum_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('favorites_added', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_level', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    print("user_stats table created successfully")

def downgrade():
    op.drop_table('user_stats')
    print("user_stats table dropped")
