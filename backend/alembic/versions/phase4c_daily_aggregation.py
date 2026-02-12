"""phase4c daily aggregation table

Revision ID: phase4c_daily_aggregation
Revises: phase4b_currency_denorm_v2
Create Date: 2026-02-12 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4c_daily_aggregation"
down_revision = "phase4b_currency_denorm_v2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daily_game_aggregation",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("total_bet", sa.Float(), nullable=False),
        sa.Column("total_win", sa.Float(), nullable=False),
        sa.Column("rounds_count", sa.Integer(), nullable=False),
        sa.Column("active_players", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "date", "provider", "currency", name="uq_daily_game_agg")
    )
    op.create_index(op.f("ix_daily_game_agg_date"), "daily_game_aggregation", ["date"], unique=False)
    op.create_index(op.f("ix_daily_game_agg_tenant_id"), "daily_game_aggregation", ["tenant_id"], unique=False)


def downgrade():
    op.drop_table("daily_game_aggregation")
