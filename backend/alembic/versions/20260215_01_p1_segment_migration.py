"""P1 Segment Migration (enum create once)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260215_01_p1_segment_migration'
down_revision = 'phase4_real_final_v56'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # CREATE TYPE once (safe)
    segment_type_enum = postgresql.ENUM(
        'INDIVIDUAL',
        'DEALER',
        name='segment_type'
    )
    segment_type_enum.create(bind, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    segment_type_enum = postgresql.ENUM(
        name='segment_type'
    )
    segment_type_enum.drop(bind, checkfirst=True)
