"""phase4 consolidated real final v46

Revision ID: phase4_real_final_v46
Revises: phase4c_daily_aggregation
Create Date: 2026-02-14 09:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4_real_final_v46"
down_revision = "phase4c_daily_aggregation"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Currency Denorm
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c['name'] for c in insp.get_columns('gameround')]
    
    if 'currency' not in columns:
        with op.batch_alter_table("gameround") as batch_op:
            batch_op.add_column(sa.Column("currency", sa.String(), nullable=True))
            batch_op.create_index(op.f("ix_gameround_currency"), ["currency"], unique=False)
        op.execute("UPDATE gameround SET currency = 'USD' WHERE currency IS NULL")
        try:
            with op.batch_alter_table("gameround") as batch_op:
                batch_op.create_index(
                    "ix_gameround_reporting_ggr",
                    ["tenant_id", "currency", "created_at"]
                )
        except:
            pass

    # 2. Aggregation Table
    try:
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
    except:
        pass


def downgrade():
    pass
