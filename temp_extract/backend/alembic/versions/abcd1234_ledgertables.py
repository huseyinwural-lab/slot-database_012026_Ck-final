"""DEPRECATED: create ledgertransaction + walletbalance tables

NOTE: This migration is kept only for historical reasons.
A newer guard migration (20260101_02) is now wired into the active Alembic chain.

Revision ID: abcd1234_ledgertables
Revises: 9e0b1a3c2f10
Create Date: 2025-12-22
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "abcd1234_ledgertables"
down_revision = "9e0b1a3c2f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "ledgertransaction" not in inspector.get_table_names():
        op.create_table(
            "ledgertransaction",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("tx_id", sa.String(), nullable=True),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("player_id", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("direction", sa.String(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("idempotency_key", sa.String(), nullable=True),
            sa.Column("provider", sa.String(), nullable=True),
            sa.Column("provider_ref", sa.String(), nullable=True),
            sa.Column("provider_event_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
            
            # Inline Constraints for SQLite compatibility during creation
            sa.UniqueConstraint("tenant_id", "player_id", "type", "idempotency_key", name="uq_ledger_tx_idempotency"),
            sa.UniqueConstraint("provider", "provider_event_id", name="uq_ledger_tx_provider_event")
        )

        # Idempotency / lookup indices
        op.create_index(
            "ix_ledger_tx_player_created_at",
            "ledgertransaction",
            ["player_id", "created_at"],
        )
        op.create_index("ix_ledger_tx_tx_id", "ledgertransaction", ["tx_id"])
        op.create_index("ix_ledger_tx_provider_ref", "ledgertransaction", ["provider_ref"])

    if "walletbalance" not in inspector.get_table_names():
        op.create_table(
            "walletbalance",
            sa.Column("tenant_id", sa.String(), primary_key=True),
            sa.Column("player_id", sa.String(), primary_key=True),
            sa.Column("currency", sa.String(length=3), primary_key=True, server_default="USD"),
            sa.Column("balance_real_available", sa.Float(), nullable=False, server_default="0"),
            sa.Column("balance_real_pending", sa.Float(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table("walletbalance")
    # No need to drop constraints explicitly if table is dropped
    op.drop_table("ledgertransaction")
