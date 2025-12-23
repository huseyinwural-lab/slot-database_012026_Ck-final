"""p0_5_gate_partial_uniques

Revision ID: 3acefa8a3e7d
Revises: 4b16b470a394
Create Date: 2025-12-23 11:13:09.017872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3acefa8a3e7d'
down_revision: Union[str, None] = '4b16b470a394'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
