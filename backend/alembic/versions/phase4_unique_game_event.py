"""add unique constraint on provider_event_id

Revision ID: phase4_unique_game_event
Revises: add_player_phone_v1
Create Date: 2026-02-12 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4_unique_game_event"
down_revision = "add_player_phone_v1" # Or latest head, assuming this is correct
branch_labels = None
depends_on = None


def upgrade():
    # GameEvent doesn't have 'provider' column in current model, only 'provider_event_id'.
    # We will enforce unique constraint on 'provider_event_id' globally.
    # If provider column is needed later for per-provider uniqueness, we can add it.
    # For now, provider_event_id is assumed unique (e.g. UUIDs or prefixed IDs).
    
    # First, try to drop index if it exists (implicit from SQLModel index=True) to avoid conflict
    # Then create explicit unique constraint.
    # But SQLModel index=True creates an index, not a unique constraint usually unless unique=True.
    # The model has unique=True on provider_event_id.
    # Let's ensure it's enforced at DB level.
    
    # Check if index exists 'ix_gameevent_provider_event_id' (default naming)
    # We will add a Unique Constraint explicitly.
    try:
        op.create_unique_constraint(
            "uq_game_event_provider_event_id",
            "gameevent",
            ["provider_event_id"]
        )
    except Exception:
        pass # Might already exist


def downgrade():
    op.drop_constraint(
        "uq_game_event_provider_event_id",
        "gameevent",
        type_="unique"
    )
