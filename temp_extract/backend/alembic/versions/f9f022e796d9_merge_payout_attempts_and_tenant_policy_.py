"""merge payout_attempts and tenant_policy heads

Revision ID: f9f022e796d9
Revises: 20251223_01_payout_attempts, 20260101_02_tenant_payment_policy
Create Date: 2025-12-23 16:02:56.535344

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = 'f9f022e796d9'
down_revision: Union[str, None] = ('20251223_01_payout_attempts', '20260101_02_tenant_payment_policy')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
