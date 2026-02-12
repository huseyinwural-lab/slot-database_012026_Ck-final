"""dummy revision to fix head history

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
    pass


def downgrade():
    pass
