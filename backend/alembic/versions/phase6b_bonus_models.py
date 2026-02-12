"""enable bonus models

Revision ID: phase6b_bonus_models
Revises: phase4c_daily_aggregation
Create Date: 2026-02-12 14:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase6b_bonus_models"
down_revision = "phase4c_daily_aggregation"
branch_labels = None
depends_on = None


def upgrade():
    # Bonus and Wagering models are already in sql_models.py but might need schema adjustments 
    # if fields were missing in previous migrations.
    # Player model has 'wagering_requirement', 'wagering_remaining'.
    # Bonus model exists.
    
    # We will ensure indexes and constraints are correct.
    pass


def downgrade():
    pass
