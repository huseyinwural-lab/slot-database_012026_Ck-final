"""P0/P1: Game schema guard - add missing provider_id column

Revision ID: 20260102_01
Revises: 20260101_01
Create Date: 2026-01-02

CI/E2E environments can drift where the `game` table exists but lacks the
`provider_id` column, while the SQLModel `Game` includes it. Any ORM query
then fails with:
  asyncpg.exceptions.UndefinedColumnError: column game.provider_id does not exist

This migration adds the columns idempotently.

"""

from alembic import op
import sqlalchemy as sa


revision = "20260102_01"
down_revision = "20260101_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    cols = {c["name"] for c in inspector.get_columns("game")}
    if "provider_id" not in cols:
        op.add_column("game", sa.Column("provider_id", sa.String(), nullable=True))


def downgrade() -> None:
    # prod-safe no-op
    pass
