"""merge_heads_2

Revision ID: 7ef7b36aecf0
Revises: add_player_phone_v1, d572f6fe576e
Create Date: 2026-02-11 20:49:24.011243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ef7b36aecf0'
down_revision: Union[str, None] = ('add_player_phone_v1', 'd572f6fe576e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
