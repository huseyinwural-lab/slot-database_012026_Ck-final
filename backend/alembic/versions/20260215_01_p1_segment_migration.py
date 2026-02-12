"""add segment_type to player

Revision ID: 20260215_01_p1_segment_migration
Revises: phase4_real_final_v56
Create Date: 2026-02-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260215_01_p1_segment_migration'
down_revision = 'phase4_real_final_v56'
branch_labels = None
depends_on = None

def upgrade():
    # Create Enum type
    segment_type = sa.Enum('INDIVIDUAL', 'DEALER', name='segment_type')
    segment_type.create(op.get_bind(), checkfirst=True)

    # Add column to player table
    op.add_column('player', sa.Column('segment_type', segment_type, nullable=True, server_default='INDIVIDUAL'))

def downgrade():
    op.drop_column('player', 'segment_type')
    sa.Enum(name='segment_type').drop(op.get_bind(), checkfirst=True)
