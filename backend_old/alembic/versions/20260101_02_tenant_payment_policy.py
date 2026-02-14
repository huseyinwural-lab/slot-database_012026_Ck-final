"""Tenant payment policy fields

Revision ID: 20260101_02_tenant_payment_policy
Revises: 20260101_01_reconciliation_runs
Create Date: 2025-12-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260101_02_tenant_payment_policy"
down_revision: Union[str, None] = "20260101_01_reconciliation_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Monetary limits stored as NUMERIC(18, 2) to match existing amount semantics
    op.add_column("tenant", sa.Column("daily_deposit_limit", sa.Numeric(18, 2), nullable=True))
    op.add_column("tenant", sa.Column("daily_withdraw_limit", sa.Numeric(18, 2), nullable=True))
    op.add_column("tenant", sa.Column("payout_retry_limit", sa.Integer(), nullable=True))
    op.add_column("tenant", sa.Column("payout_cooldown_seconds", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenant", "payout_cooldown_seconds")
    op.drop_column("tenant", "payout_retry_limit")
    op.drop_column("tenant", "daily_withdraw_limit")
    op.drop_column("tenant", "daily_deposit_limit")
