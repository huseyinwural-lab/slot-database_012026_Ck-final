"""add unique constraint on provider_event_id

Revision ID: phase4_unique_game_event
Revises: add_player_phone_v1
Create Date: 2026-02-12 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4_unique_game_event"
down_revision = "add_player_phone_v1"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_unique_constraint(
            "uq_game_event_provider_event_id",
            "gameevent",
            ["provider_event_id"]
        )
    except Exception:
        pass


def downgrade():
    try:
        op.drop_constraint(
            "uq_game_event_provider_event_id",
            "gameevent",
            type_="unique"
        )
    except:
        pass
