"""walletbalance add bonus columns

Revision ID: bee7653042ae
Revises: 20260102_04
Create Date: 2026-01-17 23:17:37.500077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bee7653042ae'
down_revision: Union[str, None] = '20260102_04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # P0-05: add bonus snapshot columns to walletbalance.
    op.add_column(
        "walletbalance",
        sa.Column(
            "balance_bonus_available",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "walletbalance",
        sa.Column(
            "balance_bonus_pending",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("walletbalance", "balance_bonus_pending")
    op.drop_column("walletbalance", "balance_bonus_available")
