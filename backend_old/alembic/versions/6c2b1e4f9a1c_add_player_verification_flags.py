"""add player verification flags

Revision ID: 6c2b1e4f9a1c
Revises: f9f022e796d9
Create Date: 2026-02-11 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "6c2b1e4f9a1c"
down_revision = "f9f022e796d9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "player",
        sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "player",
        sa.Column("sms_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade():
    op.drop_column("player", "sms_verified")
    op.drop_column("player", "email_verified")
