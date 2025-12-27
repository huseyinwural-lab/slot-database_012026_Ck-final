"""T13-001_schema_drift_reset_full

Revision ID: 3c4ee35573cd
Revises: 4de54ad60828
Create Date: 2025-12-27 00:07:49.900692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '3c4ee35573cd'
down_revision: Union[str, None] = '4de54ad60828'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name):
    bind = op.get_bind()
    insp = inspect(bind)
    return insp.has_table(table_name)

def column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def upgrade() -> None:
    # 1. POKER TABLES
    if not table_exists('pokertable'):
        op.create_table('pokertable',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('game_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('limit_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('small_blind', sa.Float(), nullable=False),
            sa.Column('big_blind', sa.Float(), nullable=False),
            sa.Column('min_buyin', sa.Float(), nullable=False),
            sa.Column('max_buyin', sa.Float(), nullable=False),
            sa.Column('currency', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('rake_profile_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('current_players', sa.Integer(), nullable=False),
            sa.Column('max_players', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_pokertable_rake_profile_id'), 'pokertable', ['rake_profile_id'], unique=False)
        op.create_index(op.f('ix_pokertable_tenant_id'), 'pokertable', ['tenant_id'], unique=False)

    if not table_exists('pokersession'):
        op.create_table('pokersession',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('player_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('table_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('buyin_total', sa.Float(), nullable=False),
            sa.Column('cashout_total', sa.Float(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['table_id'], ['pokertable.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_pokersession_player_id'), 'pokersession', ['player_id'], unique=False)
        op.create_index(op.f('ix_pokersession_table_id'), 'pokersession', ['table_id'], unique=False)
        op.create_index(op.f('ix_pokersession_tenant_id'), 'pokersession', ['tenant_id'], unique=False)

    if table_exists('table_game'):
        op.drop_index('ix_table_game_tenant_id', table_name='table_game')
        op.drop_table('table_game')

    # 2. ADMIN USER DRIFT
    if not column_exists('adminuser', 'mfa_enabled'):
        op.add_column('adminuser', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    
    # 3. AFFILIATE DRIFT
    # Affiliate table might be missing entirely if it was created via manual script but model definition was absent in previous check
    # But wait, if table exists, we check columns. If table doesn't exist, we create it?
    # The generated migration assumed 'affiliate' exists but needs columns (alter_column). 
    # This implies it thinks the table is there (from previous migrations? No, I manually created it).
    # Wait, if 'affiliate' is in 'sql_models.py' previously, maybe it was created?
    # Let's verify if affiliate table exists. If NOT, we should have seen op.create_table('affiliate').
    # We saw op.alter_column ... which means Alembic knows it exists in DB (inspection) or in Metadata?
    # Autogenerate diffs Metadata vs DB.
    # If DB has table, Metadata has table -> diff is columns.
    # If DB has table, Metadata has NO table -> diff is drop_table.
    # Since we see alter_column, it implies both have it.
    
    # We check columns:
    if not column_exists('affiliate', 'commission_type'):
        op.add_column('affiliate', sa.Column('commission_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=sa.text("'CPA'")))
    if not column_exists('affiliate', 'cpa_amount'):
        op.add_column('affiliate', sa.Column('cpa_amount', sa.Float(), nullable=False, server_default=sa.text('0.0')))
    if not column_exists('affiliate', 'cpa_threshold'):
        op.add_column('affiliate', sa.Column('cpa_threshold', sa.Float(), nullable=False, server_default=sa.text('20.0')))
    if not column_exists('affiliate', 'revshare_percent'):
        op.add_column('affiliate', sa.Column('revshare_percent', sa.Float(), nullable=False, server_default=sa.text('0.0')))

    # 4. AUDIT EVENT TYPE FIXES (Skipping for performance/risk - TEXT vs VARCHAR in SQLite is same)
    # op.alter_column('auditevent', ...) -> Skipped


def downgrade() -> None:
    # Downgrade logic is hard to make idempotent safely, sticking to basic reversal for new tables
    if table_exists('pokersession'):
        op.drop_table('pokersession')
    if table_exists('pokertable'):
        op.drop_table('pokertable')
    
    # We won't drop columns from adminuser/affiliate as they might contain data
    # and were "drifted" in.
