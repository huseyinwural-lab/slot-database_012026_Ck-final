"""schema drift guard: player + auditevent missing columns

P0: CI smoke suite can fail when tables exist but required columns are missing.
We add critical columns idempotently (IF NOT EXISTS semantics).

- player: wagering_requirement, wagering_remaining
- auditevent: actor_role, status

Revision ID: 20251231_02
Revises: 20251231_01
Create Date: 2025-12-31

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251231_02"
down_revision = "20251231_01"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
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
    # ---- player ----
    if not _column_exists("player", "wagering_requirement"):
        op.add_column(
            "player",
            sa.Column(
                "wagering_requirement",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )

    if not _column_exists("player", "wagering_remaining"):
        op.add_column(
            "player",
            sa.Column(
                "wagering_remaining",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )

    # ---- auditevent ----
    if not _column_exists("auditevent", "actor_role"):
        op.add_column(
            "auditevent",
            sa.Column("actor_role", sa.String(), nullable=True),
        )

    if not _column_exists("auditevent", "status"):
        op.add_column(
            "auditevent",
            sa.Column("status", sa.String(), nullable=True),
        )


def downgrade() -> None:
    # Best-effort downgrade (columns may not exist).
    if _column_exists("auditevent", "status"):
        op.drop_column("auditevent", "status")

    if _column_exists("auditevent", "actor_role"):
        op.drop_column("auditevent", "actor_role")

    if _column_exists("player", "wagering_remaining"):
        op.drop_column("player", "wagering_remaining")

    if _column_exists("player", "wagering_requirement"):
        op.drop_column("player", "wagering_requirement")
