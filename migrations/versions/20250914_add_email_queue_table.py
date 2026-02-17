"""add email_queue table

Revision ID: 20250914_add_email_queue
Revises: 46b5a3c74c95_add_missing_user_stats_table
Create Date: 2025-09-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250914_add_email_queue'
down_revision = '20250824_01'
branch_labels = None
depends_on = None

def upgrade():
    # Create email_queue table if not exists (idempotent guard)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'email_queue' in inspector.get_table_names():
        return
    op.create_table(
        'email_queue',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, index=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
    )
    # Explicit indexes (SQLite will have created implicit ones for PK; ensure user_id/status indexed)
    op.create_index('ix_email_queue_user_id', 'email_queue', ['user_id'])
    op.create_index('ix_email_queue_status', 'email_queue', ['status'])

def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'email_queue' in inspector.get_table_names():
        op.drop_index('ix_email_queue_user_id', table_name='email_queue')
        op.drop_index('ix_email_queue_status', table_name='email_queue')
        op.drop_table('email_queue')
