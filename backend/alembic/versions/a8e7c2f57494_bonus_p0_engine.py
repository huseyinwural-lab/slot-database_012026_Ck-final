"""bonus p0 engine

Revision ID: a8e7c2f57494
Revises: bee7653042ae
Create Date: 2026-01-17 23:37:21.803746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8e7c2f57494'
down_revision: Union[str, None] = 'bee7653042ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
