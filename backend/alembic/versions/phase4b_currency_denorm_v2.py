"""phase4b_currency_denorm_v2

Revision ID: phase4b_currency_denorm_v2
Revises: phase4_fix_columns
Create Date: 2026-02-12 11:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4b_currency_denorm_v2"
down_revision = "phase4_fix_columns"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c['name'] for c in insp.get_columns('gameround')]
    
    if 'currency' not in columns:
        with op.batch_alter_table("gameround") as batch_op:
            batch_op.add_column(sa.Column("currency", sa.String(), nullable=True))
            batch_op.create_index(op.f("ix_gameround_currency"), ["currency"], unique=False)
        
        # Set default USD
        op.execute("UPDATE gameround SET currency = 'USD' WHERE currency IS NULL")
        
        # Create reporting index
        try:
            with op.batch_alter_table("gameround") as batch_op:
                batch_op.create_index(
                    "ix_gameround_reporting_ggr",
                    ["tenant_id", "currency", "created_at"]
                )
        except Exception:
            pass


def downgrade():
    pass # No drop safety
