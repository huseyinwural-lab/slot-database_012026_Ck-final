"""create risk profile schema

Revision ID: 20260216_01_risk_profile
Revises: 20260215_02_p1_discount_migration
Create Date: 2026-02-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260216_01_risk_profile'
down_revision = '20260215_02_p1_discount_migration'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create Risk Level Enum
    # Check if type exists to avoid error in Postgres (SQLite ignores this usually)
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        risk_level = sa.Enum('LOW', 'MEDIUM', 'HIGH', name='risklevel')
        risk_level.create(bind, checkfirst=True)
    
    # 2. Create Risk Profiles Table
    op.create_table(
        'risk_profiles',
        sa.Column('user_id', sa.UUID(), nullable=False), # Assuming UUID. If SQLite, it might map to CHAR(32) or similar
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='risklevel'), server_default='LOW', nullable=True),
        sa.Column('flags', sa.JSON(), server_default='{}', nullable=True),
        sa.Column('last_event_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    op.create_index('ix_risk_profiles_tenant', 'risk_profiles', ['tenant_id'])

def downgrade():
    op.drop_index('ix_risk_profiles_tenant', table_name='risk_profiles')
    op.drop_table('risk_profiles')
    
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        sa.Enum(name='risklevel').drop(bind, checkfirst=True)
