"""add currency to gameround for reporting performance

Revision ID: phase4b_currency_denorm
Revises: phase4_fix_columns
Create Date: 2026-02-12 11:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4b_currency_denorm"
down_revision = "phase4_fix_columns"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add currency column
    with op.batch_alter_table("gameround") as batch_op:
        batch_op.add_column(sa.Column("currency", sa.String(), nullable=True))
        batch_op.create_index(op.f("ix_gameround_currency"), ["currency"], unique=False)
        
    # 2. Backfill currency (Best effort from Session or default USD)
    # In SQLite batch mode, sophisticated updates are hard.
    # We will set a default 'USD' for existing rows to enable NOT NULL logic later if needed.
    op.execute("UPDATE gameround SET currency = 'USD' WHERE currency IS NULL")
    
    # 3. Create Compound Index for Reporting (Tenant, Currency, Date)
    # Important for GGR query
    try:
        with op.batch_alter_table("gameround") as batch_op:
            batch_op.create_index(
                "ix_gameround_reporting_ggr",
                ["tenant_id", "currency", "created_at"]
            )
    except Exception:
        pass


def downgrade():
    with op.batch_alter_table("gameround") as batch_op:
        batch_op.drop_index("ix_gameround_reporting_ggr")
        batch_op.drop_index(op.f("ix_gameround_currency"))
        batch_op.drop_column("currency")
