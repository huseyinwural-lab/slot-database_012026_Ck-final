"""add risk versioning and expiry

Revision ID: 20260216_03_risk_versioning
Revises: 20260216_02_risk_history
Create Date: 2026-02-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260216_03_risk_versioning'
down_revision = '20260216_02_risk_history'
branch_labels = None
depends_on = None

def upgrade():
    # Risk Profile
    op.add_column('risk_profiles', sa.Column('risk_engine_version', sa.String(), server_default='v1', nullable=False))
    op.add_column('risk_profiles', sa.Column('override_expires_at', sa.DateTime(), nullable=True))
    
    # Risk History
    op.add_column('risk_history', sa.Column('risk_engine_version', sa.String(), server_default='v1', nullable=False))

def downgrade():
    op.drop_column('risk_history', 'risk_engine_version')
    op.drop_column('risk_profiles', 'override_expires_at')
    op.drop_column('risk_profiles', 'risk_engine_version')
