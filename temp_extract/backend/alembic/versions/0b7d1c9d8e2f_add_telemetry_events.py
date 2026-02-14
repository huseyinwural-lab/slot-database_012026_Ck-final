"""add telemetry events table

Revision ID: 0b7d1c9d8e2f
Revises: 6c2b1e4f9a1c
Create Date: 2026-02-11 12:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0b7d1c9d8e2f"
down_revision = "6c2b1e4f9a1c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("event_name", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_telemetry_events_tenant_id", "telemetry_events", ["tenant_id"])


def downgrade():
    op.drop_index("ix_telemetry_events_tenant_id", table_name="telemetry_events")
    op.drop_table("telemetry_events")
