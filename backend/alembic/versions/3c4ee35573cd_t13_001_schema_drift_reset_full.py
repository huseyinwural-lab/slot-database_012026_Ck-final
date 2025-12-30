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

    # MISSING TABLES FROM PREVIOUS SPRINTS (RESTORATION)
    if not table_exists('pokertournament'):
        op.create_table('pokertournament',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('game_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('limit_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('buy_in', sa.Float(), nullable=False),
            sa.Column('fee', sa.Float(), nullable=False),
            sa.Column('currency', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('guaranteed_prize', sa.Float(), nullable=True),
            sa.Column('starting_chips', sa.Integer(), nullable=False),
            sa.Column('min_players', sa.Integer(), nullable=False),
            sa.Column('max_players', sa.Integer(), nullable=False),
            sa.Column('start_at', sa.DateTime(), nullable=False),
            sa.Column('late_reg_until', sa.DateTime(), nullable=True),
            sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('prize_pool_total', sa.Float(), nullable=False),
            sa.Column('entrants_count', sa.Integer(), nullable=False),
            sa.Column('payout_report', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_pokertournament_status'), 'pokertournament', ['status'], unique=False)
        op.create_index(op.f('ix_pokertournament_tenant_id'), 'pokertournament', ['tenant_id'], unique=False)

    if not table_exists('tournamentregistration'):
        op.create_table('tournamentregistration',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tournament_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('player_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('buyin_amount', sa.Float(), nullable=False),
            sa.Column('fee_amount', sa.Float(), nullable=False),
            sa.Column('registered_at', sa.DateTime(), nullable=False),
            sa.Column('tx_ref_buyin', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tx_ref_fee', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.ForeignKeyConstraint(['tournament_id'], ['pokertournament.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_tournamentregistration_player_id'), 'tournamentregistration', ['player_id'], unique=False)
        op.create_index(op.f('ix_tournamentregistration_tenant_id'), 'tournamentregistration', ['tenant_id'], unique=False)
        op.create_index(op.f('ix_tournamentregistration_tournament_id'), 'tournamentregistration', ['tournament_id'], unique=False)

    if not table_exists('risksignal'):
        op.create_table('risksignal',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('player_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('target_resource_type', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('target_resource_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('signal_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('severity', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('evidence_payload', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_risksignal_player_id'), 'risksignal', ['player_id'], unique=False)
        op.create_index(op.f('ix_risksignal_tenant_id'), 'risksignal', ['tenant_id'], unique=False)

    if not table_exists('rakeprofile'):
        op.create_table('rakeprofile',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('game_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('percentage', sa.Float(), nullable=False),
            sa.Column('cap', sa.Float(), nullable=False),
            sa.Column('rules', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_rakeprofile_name'), 'rakeprofile', ['name'], unique=False)
        op.create_index(op.f('ix_rakeprofile_tenant_id'), 'rakeprofile', ['tenant_id'], unique=False)

    if not table_exists('pokerhandaudit'):
        op.create_table('pokerhandaudit',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('tenant_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('provider_hand_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('table_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('game_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('pot_total', sa.Float(), nullable=False),
            sa.Column('rake_collected', sa.Float(), nullable=False),
            sa.Column('rake_profile_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column('winners', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['rake_profile_id'], ['rakeprofile.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_pokerhandaudit_provider_hand_id'), 'pokerhandaudit', ['provider_hand_id'], unique=False)
        op.create_index(op.f('ix_pokerhandaudit_tenant_id'), 'pokerhandaudit', ['tenant_id'], unique=False)

    if table_exists('table_game'):
        op.drop_index('ix_table_game_tenant_id', table_name='table_game')
        op.drop_table('table_game')

    # 2. ADMIN USER DRIFT
    if not column_exists('adminuser', 'mfa_enabled'):
        op.add_column('adminuser', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # 3. AFFILIATE DRIFT
    if not column_exists('affiliate', 'commission_type'):
        op.add_column('affiliate', sa.Column('commission_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=sa.text("'CPA'")))
    if not column_exists('affiliate', 'cpa_amount'):
        op.add_column('affiliate', sa.Column('cpa_amount', sa.Float(), nullable=False, server_default=sa.text('0.0')))
    if not column_exists('affiliate', 'cpa_threshold'):
        op.add_column('affiliate', sa.Column('cpa_threshold', sa.Float(), nullable=False, server_default=sa.text('20.0')))
    if not column_exists('affiliate', 'revshare_percent'):
        op.add_column('affiliate', sa.Column('revshare_percent', sa.Float(), nullable=False, server_default=sa.text('0.0')))


def downgrade() -> None:
    # Downgrade logic is hard to make idempotent safely, sticking to basic reversal for new tables
    if table_exists('pokersession'):
        op.drop_table('pokersession')
    if table_exists('pokertable'):
        op.drop_table('pokertable')
    
    # We won't drop columns from adminuser/affiliate as they might contain data
    # and were "drifted" in.
