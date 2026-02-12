"""fix missing created_at in gameevent

Revision ID: phase4_fix_columns
Revises: phase4_data_integrity
Create Date: 2026-02-12 10:30:00
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "phase4_fix_columns"
down_revision = "phase4_data_integrity"
branch_labels = None
depends_on = None


def upgrade():
    # Check if created_at exists in gameevent
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c['name'] for c in insp.get_columns('gameevent')]
    
    if 'created_at' not in columns:
        with op.batch_alter_table("gameevent") as batch_op:
            batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
            # Set default for existing
            batch_op.execute("UPDATE gameevent SET created_at = datetime('now') WHERE created_at IS NULL")


def downgrade():
    pass # No drop to be safe
