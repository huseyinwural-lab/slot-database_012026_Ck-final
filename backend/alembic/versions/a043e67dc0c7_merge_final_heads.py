"""merge_final_heads

Revision ID: a043e67dc0c7
Revises: phase4b_currency_denorm_v2, phase4c_daily_agg_fixed
Create Date: 2026-02-12 14:25:40.223392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a043e67dc0c7'
down_revision: Union[str, None] = ('phase4b_currency_denorm_v2', 'phase4c_daily_agg_fixed')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
