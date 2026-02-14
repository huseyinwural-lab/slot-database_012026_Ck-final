"""T14_poker_risk_mtt

Revision ID: 94870c5756db
Revises: 8b10a4b2c29b
Create Date: 2025-12-27 00:18:43.762366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '94870c5756db'
down_revision: Union[str, None] = '8b10a4b2c29b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def upgrade() -> None:
    # Adding Re-entry fields to PokerTournament
    if not column_exists('pokertournament', 'reentry_max'):
        op.add_column('pokertournament', sa.Column('reentry_max', sa.Integer(), nullable=False, server_default=sa.text('0')))
        
    if not column_exists('pokertournament', 'reentry_price'):
        op.add_column('pokertournament', sa.Column('reentry_price', sa.Float(), nullable=True))

    # Skipping other auto-generated changes to avoid drift noise
    # (Affiliate/AdminUser changes are already applied via drift reset or manual patch, no need to touch)

def downgrade() -> None:
    if column_exists('pokertournament', 'reentry_price'):
        op.drop_column('pokertournament', 'reentry_price')
    if column_exists('pokertournament', 'reentry_max'):
        op.drop_column('pokertournament', 'reentry_max')
