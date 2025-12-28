"""finance state machine and balance split

Revision ID: 9e0b1a3c2f10
Revises: 7b01f4a2c9e1
Create Date: 2025-12-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e0b1a3c2f10"
down_revision: Union[str, None] = "7b01f4a2c9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def upgrade() -> None:
    # --- Player balance split ---
    op.add_column("player", sa.Column("balance_real_available", sa.Float(), nullable=False, server_default="0"))
    op.add_column("player", sa.Column("balance_real_held", sa.Float(), nullable=False, server_default="0"))

    # Backfill: move existing balance_real -> balance_real_available, held=0 (COALESCE for safety)
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE player SET balance_real_available = COALESCE(balance_real, 0), balance_real_held = 0"
    ))

    # --- Transaction state/idempotency extensions ---
    if _is_sqlite():
        # Use quoted table name and explicit ALTER for SQLite
        op.execute('ALTER TABLE "transaction" ADD COLUMN state VARCHAR NOT NULL DEFAULT "created"')
        op.execute('ALTER TABLE "transaction" ADD COLUMN idempotency_key VARCHAR NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN provider VARCHAR NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN provider_event_id VARCHAR NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN review_reason TEXT NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN reviewed_by VARCHAR NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN reviewed_at DATETIME NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN metadata JSON NULL')
        op.execute('ALTER TABLE "transaction" ADD COLUMN updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)')
    else:
        op.add_column("transaction", sa.Column("state", sa.String(), nullable=False, server_default="created"))
        op.add_column("transaction", sa.Column("idempotency_key", sa.String(), nullable=True))
        op.add_column("transaction", sa.Column("provider", sa.String(), nullable=True))
        op.add_column("transaction", sa.Column("provider_event_id", sa.String(), nullable=True))
        op.add_column("transaction", sa.Column("review_reason", sa.Text(), nullable=True))
        op.add_column("transaction", sa.Column("reviewed_by", sa.String(), nullable=True))
        op.add_column("transaction", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
        op.add_column("transaction", sa.Column("metadata", sa.JSON(), nullable=True))
        op.add_column("transaction", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    # Backfill minimal state from existing status/type (Fixed quotes for PostgreSQL compatibility)
    conn.execute(sa.text(
        "UPDATE \"transaction\" SET state = 'completed' WHERE type = 'deposit' AND status = 'completed'"
    ))
    conn.execute(sa.text(
        "UPDATE \"transaction\" SET state = 'requested' WHERE type = 'withdrawal' AND status = 'pending'"
    ))

    # Partial unique indexes for idempotency and provider events
    op.create_index(
        "ux_tx_player_id_idempotency_key_not_null",
        "transaction",
        ["player_id", "idempotency_key"],
        unique=True,
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "ux_tx_provider_event_not_null",
        "transaction",
        ["provider", "provider_event_id"],
        unique=True,
        sqlite_where=sa.text("provider_event_id IS NOT NULL"),
        postgresql_where=sa.text("provider_event_id IS NOT NULL"),
    )


def downgrade() -> None:
    # Drop partial unique indexes
    op.drop_index("ux_tx_provider_event_not_null", table_name="transaction")
    op.drop_index("ux_tx_player_id_idempotency_key_not_null", table_name="transaction")

    # Drop transaction extension columns
    op.drop_column("transaction", "updated_at")
    op.drop_column("transaction", "metadata")
    op.drop_column("transaction", "reviewed_at")
    op.drop_column("transaction", "reviewed_by")
    op.drop_column("transaction", "review_reason")
    op.drop_column("transaction", "provider_event_id")
    op.drop_column("transaction", "provider")
    op.drop_column("transaction", "idempotency_key")
    op.drop_column("transaction", "state")

    # Drop player balance split columns
    op.drop_column("player", "balance_real_held")
    op.drop_column("player", "balance_real_available")
