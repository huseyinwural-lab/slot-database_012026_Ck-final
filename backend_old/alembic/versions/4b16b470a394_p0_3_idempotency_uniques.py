"""p0_3_idempotency_uniques

Revision ID: 4b16b470a394
Revises: 20260101_01_reconciliation_runs
Create Date: 2025-12-23 09:35:25.923372

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4b16b470a394'
down_revision: Union[str, None] = '20260101_01_reconciliation_runs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add idempotency UNIQUE constraints.

    SQLite does not support ALTER TABLE ADD CONSTRAINT in-place. In dev/test we
    rely on application-level idempotency and separate Postgres hardening
    (partial indexes documented in 3acefa8a3e7d). For real databases that do
    support constraints (e.g. Postgres), we apply them here.
    """

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":  # no-op on SQLite
        return

    # LedgerTransaction idempotency unique
    op.create_unique_constraint(
        "uq_ledger_idem",
        "ledgertransaction",
        ["tenant_id", "player_id", "type", "idempotency_key"],
    )

    # Provider event unique for webhook replay-safety
    op.create_unique_constraint(
        "uq_ledger_provider_event",
        "ledgertransaction",
        ["provider", "provider_event_id"],
    )

    # Transaction (payment) create idempotency uniques
    op.create_unique_constraint(
        "uq_tx_deposit_idem",
        "transaction",
        ["tenant_id", "idempotency_key", "type"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":  # no-op on SQLite
        return

    op.drop_constraint("uq_tx_deposit_idem", "transaction", type_="unique")
    op.drop_constraint("uq_ledger_provider_event", "ledgertransaction", type_="unique")
    op.drop_constraint("uq_ledger_idem", "ledgertransaction", type_="unique")
