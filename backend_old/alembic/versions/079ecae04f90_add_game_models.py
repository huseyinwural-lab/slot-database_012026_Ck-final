"""Add Game Models

Revision ID: 079ecae04f90
Revises: f9f022e796d9
Create Date: 2025-12-26 17:27:42.172432

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '079ecae04f90'
down_revision: Union[str, None] = 'f9f022e796d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PREVIOUSLY: This migration attempted to drop numerous tables (player, game, etc.)
    # which caused FK constraint failures and data loss risk.
    # FIX: Converted to NO-OP.
    # The schema state is assumed to be correct or handled by subsequent migrations.
    pass


def downgrade() -> None:
    pass
