"""p0_3_idempotency_uniques

Revision ID: 4b16b470a394
Revises: 20260101_01_reconciliation_runs
Create Date: 2025-12-23 09:35:25.923372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b16b470a394'
down_revision: Union[str, None] = '20260101_01_reconciliation_runs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
