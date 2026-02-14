"""merge_heads

Revision ID: d572f6fe576e
Revises: 0b7d1c9d8e2f, bc11f2c6a3aa
Create Date: 2026-02-11 20:05:36.049863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd572f6fe576e'
down_revision: Union[str, None] = ('0b7d1c9d8e2f', 'bc11f2c6a3aa')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
