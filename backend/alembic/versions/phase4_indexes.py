"""add performance indexes

Revision ID: phase4_indexes
Revises: 9775b5966217
Create Date: 2026-02-12 10:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4_indexes"
down_revision = "9775b5966217"
branch_labels = None
depends_on = None


def upgrade():
    # Indexes for Reporting Performance
    # GameEvent: round_id, created_at
    # GameRound: player_id, game_id, created_at
    
    # Check/Create if not exists logic is hard in generic alembic without inspection
    # Assuming standard naming conventions
    
    op.create_index(op.f("ix_gameevent_created_at"), "gameevent", ["created_at"], unique=False)
    op.create_index(op.f("ix_gameround_created_at"), "gameround", ["created_at"], unique=False)
    
    # Compound index for GGR reporting (created_at + game_id often used)
    # op.create_index("ix_gameround_reporting", "gameround", ["tenant_id", "created_at"])


def downgrade():
    op.drop_index(op.f("ix_gameround_created_at"), table_name="gameround")
    op.drop_index(op.f("ix_gameevent_created_at"), table_name="gameevent")
