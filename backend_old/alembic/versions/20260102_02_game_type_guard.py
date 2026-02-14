"""P0/P1: Game schema guard - add missing type column

Revision ID: 20260102_02
Revises: 20260102_01
Create Date: 2026-01-02

CI/E2E environments can drift where the `game` table exists but lacks columns
referenced by the SQLModel `Game` (e.g. `type`). This breaks `/api/v1/ci/seed` and
any game listing endpoints with:
  asyncpg.exceptions.UndefinedColumnError: column game.type does not exist

This migration adds `game.type` idempotently and backfills from legacy
`core_type` if it exists.

"""

from alembic import op
import sqlalchemy as sa


revision = "20260102_02"
down_revision = "20260102_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    cols = {c["name"] for c in inspector.get_columns("game")}

    if "type" not in cols:
        op.add_column("game", sa.Column("type", sa.String(length=64), nullable=True))

        # Backfill from a legacy column name if present
        if "core_type" in cols:
            op.execute("UPDATE game SET type = core_type WHERE type IS NULL")

        # Default for existing rows if still NULL
        op.execute("UPDATE game SET type = 'slot' WHERE type IS NULL")

        # index helps filtering
        op.create_index("ix_game_type", "game", ["type"], unique=False)


def downgrade() -> None:
    # prod-safe no-op
    pass
