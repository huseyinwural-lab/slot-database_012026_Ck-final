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
    # Prod-safety invariant: migrations must be idempotent.

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    # 1) bonuscampaign columns
    if "bonuscampaign" in tables:
        cols = {c["name"] for c in inspector.get_columns("bonuscampaign")}
        if 'bet_amount' not in cols:
            op.add_column("bonuscampaign", sa.Column("bet_amount", sa.Float(), nullable=True))
        if 'spin_count' not in cols:
            op.add_column("bonuscampaign", sa.Column("spin_count", sa.Integer(), nullable=True))
        if 'max_uses' not in cols:
            op.add_column("bonuscampaign", sa.Column("max_uses", sa.Integer(), nullable=True))

    # 2) bonusgrant columns
    if "bonusgrant" in tables:
        cols = {c["name"] for c in inspector.get_columns("bonusgrant")}
        if 'bonus_type' not in cols:
            op.add_column("bonusgrant", sa.Column("bonus_type", sa.String(), nullable=True))
        if 'remaining_uses' not in cols:
            op.add_column("bonusgrant", sa.Column("remaining_uses", sa.Integer(), nullable=True))

    # 3) campaign ↔ games join table
    if "bonuscampaign" in tables and "game" in tables and "bonuscampaigngame" not in tables:
        op.create_table(
            "bonuscampaigngame",
            sa.Column("campaign_id", sa.String(), nullable=False),
            sa.Column("game_id", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["campaign_id"], ["bonuscampaign.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["game.id"]),
            sa.PrimaryKeyConstraint("campaign_id", "game_id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='bonuscampaigngame'")).fetchone()
    if existing:
        op.drop_table("bonuscampaigngame")

    op.drop_column("bonusgrant", "remaining_uses")
    # no-op: constraint not created on SQLite
    op.drop_column("bonusgrant", "bonus_type")

    op.drop_column("bonuscampaign", "max_uses")
    op.drop_column("bonuscampaign", "spin_count")
    op.drop_column("bonuscampaign", "bet_amount")
    # no-op: constraint not created on SQLite
    # bonuscampaign.bonus_type pre-existed; do not drop here.
