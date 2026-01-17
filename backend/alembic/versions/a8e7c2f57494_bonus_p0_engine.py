"""bonus p0 engine

Revision ID: a8e7c2f57494
Revises: bee7653042ae
Create Date: 2026-01-17 23:37:21.803746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8e7c2f57494'
down_revision: Union[str, None] = 'bee7653042ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # P0 Bonus engine additions
    
    # 1) bonuscampaign: enum-ish bonus_type (already exists in some envs)
    # NOTE (SQLite): cannot ALTER TABLE to add CHECK constraints. Enforce via app-level validation.
    op.add_column("bonuscampaign", sa.Column("bet_amount", sa.Float(), nullable=True))
    op.add_column("bonuscampaign", sa.Column("spin_count", sa.Integer(), nullable=True))
    op.add_column("bonuscampaign", sa.Column("max_uses", sa.Integer(), nullable=True))

    # 2) bonusgrant: add remaining_uses + bonus_type for deterministic consume
    op.add_column(
        "bonusgrant",
        sa.Column("bonus_type", sa.String(), nullable=True),
    )
    # NOTE (SQLite): cannot ALTER TABLE to add CHECK constraints. Enforce via app-level validation.
    op.add_column("bonusgrant", sa.Column("remaining_uses", sa.Integer(), nullable=True))

    # 3) campaign ↔ games (normalized)
    # NOTE: SQLite has no CREATE TABLE IF NOT EXISTS via alembic op. If table exists (partial migration), skip.
    bind = op.get_bind()
    existing = bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='bonuscampaigngame'")).fetchone()
    if not existing:
        op.create_table(
            "bonuscampaigngame",
            sa.Column("campaign_id", sa.String(), nullable=False),
            sa.Column("game_id", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["campaign_id"], ["bonuscampaign.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
            sa.PrimaryKeyConstraint("campaign_id", "game_id"),
        )


def downgrade() -> None:
    op.drop_table("bonuscampaigngame")

    op.drop_column("bonusgrant", "remaining_uses")
    # no-op: constraint not created on SQLite
    op.drop_column("bonusgrant", "bonus_type")

    op.drop_column("bonuscampaign", "max_uses")
    op.drop_column("bonuscampaign", "spin_count")
    op.drop_column("bonuscampaign", "bet_amount")
    # no-op: constraint not created on SQLite
    # bonuscampaign.bonus_type pre-existed; do not drop here.
