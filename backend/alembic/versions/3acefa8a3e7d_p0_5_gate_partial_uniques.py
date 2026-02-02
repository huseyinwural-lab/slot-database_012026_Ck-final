"""p0_5_gate_partial_uniques

Revision ID: 3acefa8a3e7d
Revises: 4b16b470a394
Create Date: 2025-12-23 11:13:09.017872

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '3acefa8a3e7d'
down_revision: Union[str, None] = '4b16b470a394'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE: This migration is intentionally a no-op for SQLite/dev. In
    # production Postgres, idempotency_key and provider_event_id MUST be
    # hardened either via NOT NULL constraints or partial unique indexes,
    # for example:
    #
    #   ALTER TABLE ledgertransaction
    #   ALTER COLUMN idempotency_key SET NOT NULL;
    #
    #   CREATE UNIQUE INDEX uq_ledger_provider_event_partial
    #   ON ledgertransaction(provider, provider_event_id)
    #   WHERE provider_event_id IS NOT NULL;
    #
    #   CREATE UNIQUE INDEX uq_ledger_idem_partial
    #   ON ledgertransaction(tenant_id, player_id, type, idempotency_key)
    #   WHERE idempotency_key IS NOT NULL;
    #
    #   ALTER TABLE transaction
    #   ALTER COLUMN idempotency_key SET NOT NULL;
    #
    #   CREATE UNIQUE INDEX uq_tx_deposit_idem_partial
    #   ON transaction(tenant_id, idempotency_key, type)
    #   WHERE idempotency_key IS NOT NULL;
    #
    # These statements are documented here for the Ops/DBA team and should be
    # applied in the Postgres environment. Running them against SQLite is not
    # meaningful, so this migration keeps the dev schema unchanged.
    pass


def downgrade() -> None:
    # Downgrade for Postgres would require dropping the partial indexes and
    # relaxing NOT NULL constraints, which is outside the scope of the
    # application codebase. No-op here as well.
    pass
