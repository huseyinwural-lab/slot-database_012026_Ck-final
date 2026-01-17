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
    
    # 1) bonuscampaign: add structured fields + enum-ish bonus_type (nullable for legacy)
    op.add_column(
        "bonuscampaign",
        sa.Column("bonus_type", sa.String(), nullable=True),
    )
    op.create_check_constraint(
        "ck_bonuscampaign_bonus_type_allowed",
        "bonuscampaign",
        "bonus_type in ('FREE_SPIN','FREE_BET','MANUAL_CREDIT') OR bonus_type IS NULL",
    )
    op.add_column("bonuscampaign", sa.Column("bet_amount", sa.Float(), nullable=True))
    op.add_column("bonuscampaign", sa.Column("spin_count", sa.Integer(), nullable=True))
    op.add_column("bonuscampaign", sa.Column("max_uses", sa.Integer(), nullable=True))

    # 2) bonusgrant: add remaining_uses + bonus_type for deterministic consume
    op.add_column(
        "bonusgrant",
        sa.Column("bonus_type", sa.String(), nullable=True),
    )
    op.create_check_constraint(
        "ck_bonusgrant_bonus_type_allowed",
        "bonusgrant",
        "bonus_type in ('FREE_SPIN','FREE_BET','MANUAL_CREDIT') OR bonus_type IS NULL",
    )
    op.add_column("bonusgrant", sa.Column("remaining_uses", sa.Integer(), nullable=True))

    # 3) campaign ↔ games (normalized)
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
    op.drop_constraint("ck_bonusgrant_bonus_type_allowed", "bonusgrant", type_="check")
    op.drop_column("bonusgrant", "bonus_type")

    op.drop_column("bonuscampaign", "max_uses")
    op.drop_column("bonuscampaign", "spin_count")
    op.drop_column("bonuscampaign", "bet_amount")
    op.drop_constraint("ck_bonuscampaign_bonus_type_allowed", "bonuscampaign", type_="check")
    op.drop_column("bonuscampaign", "bonus_type")
