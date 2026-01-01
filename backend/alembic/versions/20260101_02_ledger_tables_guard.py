"""P0: Ledger tables guard (ledgertransaction + walletbalance)

Revision ID: 20260101_02
Revises: 20260101_01
Create Date: 2026-01-01

This migration makes the money-path deterministic in fresh Postgres environments.
Some environments had ledger models in code but missing physical tables,
causing deposit flows to 500 with relation-does-not-exist errors.

We create the two core tables idempotently.

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260101_02"
down_revision = "20251231_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    # LedgerTransaction (immutable append-only event log)
    if "ledgertransaction" not in existing:
        op.create_table(
            "ledgertransaction",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("tx_id", sa.String(), nullable=True),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("player_id", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("direction", sa.String(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("idempotency_key", sa.String(), nullable=True),
            sa.Column("provider", sa.String(), nullable=True),
            sa.Column("provider_ref", sa.String(), nullable=True),
            sa.Column("provider_event_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        )

        op.create_index(
            "ix_ledger_tx_player_created_at",
            "ledgertransaction",
            ["player_id", "created_at"],
        )
        op.create_index("ix_ledger_tx_tx_id", "ledgertransaction", ["tx_id"])
        op.create_index("ix_ledger_tx_provider_ref", "ledgertransaction", ["provider_ref"])

    # WalletBalance (materialized snapshot)
    if "walletbalance" not in existing:
        op.create_table(
            "walletbalance",
            sa.Column("tenant_id", sa.String(), primary_key=True),
            sa.Column("player_id", sa.String(), primary_key=True),
            sa.Column("currency", sa.String(length=3), primary_key=True, server_default=sa.text("'USD'")),
            sa.Column("balance_real_available", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("balance_real_pending", sa.Float(), nullable=False, server_default=sa.text("0")),
            sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    # Intentionally no-op (prod-safe). Dropping financial tables is not safe.
    pass
