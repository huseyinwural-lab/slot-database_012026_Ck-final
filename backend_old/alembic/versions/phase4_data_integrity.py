"""phase4 data integrity with composite unique constraint

Revision ID: phase4_data_integrity
Revises: phase4_indexes_fixed
Create Date: 2026-02-12 10:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4_data_integrity"
down_revision = "phase4_indexes_fixed"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add columns to GameEvent: provider, player_id
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table("gameevent") as batch_op:
        batch_op.add_column(sa.Column("provider", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("player_id", sa.String(), nullable=True))
        
        batch_op.create_index(op.f("ix_gameevent_provider"), ["provider"], unique=False)
        batch_op.create_index(op.f("ix_gameevent_player_id"), ["player_id"], unique=False)

    # 2. Add Composite Unique Constraint (provider, provider_event_id)
    # First, populate 'provider' for existing rows (if any) to avoid constraint failure
    # Defaulting to 'unknown' or 'simulator'
    op.execute("UPDATE gameevent SET provider = 'simulator' WHERE provider IS NULL")
    
    # Drop old constraint if exists (from phase4_unique_game_event)
    try:
        with op.batch_alter_table("gameevent") as batch_op:
            batch_op.drop_constraint("uq_game_event_provider_event_id", type_="unique")
    except Exception:
        pass

    # Create new composite constraint
    with op.batch_alter_table("gameevent") as batch_op:
        batch_op.create_unique_constraint(
            "uq_game_event_provider_event_composite",
            ["provider", "provider_event_id"]
        )


def downgrade():
    with op.batch_alter_table("gameevent") as batch_op:
        batch_op.drop_constraint("uq_game_event_provider_event_composite", type_="unique")
        batch_op.drop_index(op.f("ix_gameevent_player_id"))
        batch_op.drop_index(op.f("ix_gameevent_provider"))
        batch_op.drop_column("player_id")
        batch_op.drop_column("provider")
    
    # Restore old constraint? (Optional)
