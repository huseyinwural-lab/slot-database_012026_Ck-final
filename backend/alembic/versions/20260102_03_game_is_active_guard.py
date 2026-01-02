"""P0: Game schema guard - add missing is_active column

Revision ID: 20260102_03
Revises: 20260102_02
Create Date: 2026-01-02

CI/E2E environments can drift where the `game` table exists but lacks
columns referenced by SQLModel (e.g. `is_active`). Any ORM query then fails
with `UndefinedColumnError: column game.is_active does not exist`.

This migration adds the column idempotently and backfills deterministic
values.

"""

from alembic import op
import sqlalchemy as sa


revision = "20260102_03"
down_revision = "20260102_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = set(inspector.get_table_names())
    if "game" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("game")}

    if "is_active" not in cols:
        op.add_column("game", sa.Column("is_active", sa.Boolean(), nullable=True))
        op.execute("UPDATE game SET is_active = TRUE WHERE is_active IS NULL")
        op.alter_column("game", "is_active", nullable=False)
        op.alter_column("game", "is_active", server_default=sa.text("TRUE"))


def downgrade() -> None:
    # prod-safe no-op
    pass
