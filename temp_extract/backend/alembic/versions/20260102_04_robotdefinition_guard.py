"""P0: RobotDefinition schema guard - add missing columns

Revision ID: 20260102_04
Revises: 20260102_03
Create Date: 2026-01-02

CI/E2E environments can drift where the `robotdefinition` table exists but
lacks columns referenced by SQLModel (e.g. `is_active`, `updated_at`,
`config_hash`). Any ORM query then fails with UndefinedColumnError.

This migration adds these columns idempotently and backfills deterministic
values.

"""

from alembic import op
import sqlalchemy as sa


revision = "20260102_04"
down_revision = "20260102_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = set(inspector.get_table_names())
    if "robotdefinition" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("robotdefinition")}

    if "is_active" not in cols:
        op.add_column("robotdefinition", sa.Column("is_active", sa.Boolean(), nullable=True))
        op.execute("UPDATE robotdefinition SET is_active = TRUE WHERE is_active IS NULL")
        op.alter_column("robotdefinition", "is_active", nullable=False)
        op.alter_column("robotdefinition", "is_active", server_default=sa.text("TRUE"))

    if "updated_at" not in cols:
        op.add_column("robotdefinition", sa.Column("updated_at", sa.DateTime(), nullable=True))
        op.execute("UPDATE robotdefinition SET updated_at = NOW() WHERE updated_at IS NULL")
        op.alter_column("robotdefinition", "updated_at", nullable=False)

    if "config_hash" not in cols:
        op.add_column("robotdefinition", sa.Column("config_hash", sa.String(), nullable=True))
        op.execute("UPDATE robotdefinition SET config_hash = 'legacy' WHERE config_hash IS NULL")
        op.alter_column("robotdefinition", "config_hash", nullable=False)


def downgrade() -> None:
    # prod-safe no-op
    pass
