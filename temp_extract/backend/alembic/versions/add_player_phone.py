"""add player phone column

Revision ID: add_player_phone_v1
Revises: 0b7d1c9d8e2f
Create Date: 2026-02-11 12:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "add_player_phone_v1"
down_revision = "0b7d1c9d8e2f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "player",
        sa.Column("phone", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_player_phone"), "player", ["phone"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_player_phone"), table_name="player")
    op.drop_column("player", "phone")
