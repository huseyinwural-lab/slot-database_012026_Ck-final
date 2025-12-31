"""add player wagering columns

P0: CI smoke suite fails because the `player` table exists but is missing
`wagering_requirement` (and related) columns. Earlier migrations only created the
`player` table if it didn't already exist, which can leave schema drift.

This migration is idempotent and safe to run on Postgres.

Revision ID: 20251231_01
Revises: 20251230_01
Create Date: 2025-12-31

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251231_01"
down_revision = "20251230_01"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    # Works on Postgres
    res = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :t
              AND column_name = :c
            LIMIT 1
            """
        ),
        {"t": table_name, "c": column_name},
    ).fetchone()
    return res is not None


def upgrade() -> None:
    # These columns are referenced by the Player ORM model and are required for
    # registration/login flows.
    if not _column_exists("player", "wagering_requirement"):
        op.add_column(
            "player",
            sa.Column("wagering_requirement", sa.Float(), nullable=False, server_default=sa.text("0")),
        )

    if not _column_exists("player", "wagering_remaining"):
        op.add_column(
            "player",
            sa.Column("wagering_remaining", sa.Float(), nullable=False, server_default=sa.text("0")),
        )


def downgrade() -> None:
    # Best-effort downgrade (columns may not exist).
    if _column_exists("player", "wagering_remaining"):
        op.drop_column("player", "wagering_remaining")

    if _column_exists("player", "wagering_requirement"):
        op.drop_column("player", "wagering_requirement")
