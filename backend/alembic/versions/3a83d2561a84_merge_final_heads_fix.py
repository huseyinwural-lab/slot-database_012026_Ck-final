"""merge_final_heads_fix

Revision ID: 3a83d2561a84
Revises: a043e67dc0c7, phase4c_daily_aggregation
Create Date: 2026-02-12 14:26:17.788852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a83d2561a84'
down_revision: Union[str, None] = ('a043e67dc0c7', 'phase4c_daily_aggregation')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
