"""merge_phase4_fix

Revision ID: 552e5076c12a
Revises: phase4c_daily_aggregation
Create Date: 2026-02-12 14:24:42.670680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '552e5076c12a'
down_revision: Union[str, None] = 'phase4c_daily_aggregation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
