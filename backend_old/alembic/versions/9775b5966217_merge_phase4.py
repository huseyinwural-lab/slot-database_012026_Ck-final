"""merge_phase4

Revision ID: 9775b5966217
Revises: 7ef7b36aecf0, phase4_unique_game_event
Create Date: 2026-02-12 08:26:31.138486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9775b5966217'
down_revision: Union[str, None] = ('7ef7b36aecf0', 'phase4_unique_game_event')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
