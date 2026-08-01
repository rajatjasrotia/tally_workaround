"""add item tracking columns

Revision ID: 0001_add_item_columns
Revises: 
Create Date: 2026-08-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_item_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add total_added and sold_count with default 0
    op.add_column('item', sa.Column('total_added', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('item', sa.Column('sold_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('item', 'sold_count')
    op.drop_column('item', 'total_added')
