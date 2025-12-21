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


def upgrade() -> None:
    # --- Player balance split ---
    op.add_column("player", sa.Column("balance_real_available", sa.Float(), nullable=False, server_default="0"))
    op.add_column("player", sa.Column("balance_real_held", sa.Float(), nullable=False, server_default="0"))

    # Backfill: move existing balance_real -> balance_real_available, held=0
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE player SET balance_real_available = balance_real, balance_real_held = 0"))

    # --- Transaction state/idempotency extensions ---
    op.add_column("transaction", sa.Column("state", sa.String(), nullable=False, server_default="created"))
    op.add_column("transaction", sa.Column("idempotency_key", sa.String(), nullable=True))
    op.add_column("transaction", sa.Column("provider", sa.String(), nullable=True))
    op.add_column("transaction", sa.Column("provider_event_id", sa.String(), nullable=True))
    op.add_column("transaction", sa.Column("review_reason", sa.Text(), nullable=True))
    op.add_column("transaction", sa.Column("reviewed_by", sa.String(), nullable=True))
    op.add_column("transaction", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("transaction", sa.Column("metadata", sa.JSON(), nullable=True))
    op.add_column("transaction", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    # Backfill minimal state from existing status/type
    conn.execute(
        sa.text(
            "UPDATE transaction SET state = 'completed' WHERE type = 'deposit' AND status = 'completed'"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE transaction SET state = 'requested' WHERE type = 'withdrawal' AND status = 'pending'"
        )
    )

    # Partial unique constraints for idempotency and provider events
    op.create_unique_constraint(
        "uq_transaction_player_id_idempotency_key_not_null",
        "transaction",
        ["player_id", "idempotency_key"],
        deferrable=False,
        initially=None,
    )
    op.create_unique_constraint(
        "uq_transaction_provider_event_not_null",
        "transaction",
        ["provider", "provider_event_id"],
        deferrable=False,
        initially=None,
    )


def downgrade() -> None:
    # Drop unique constraints
    op.drop_constraint("uq_transaction_provider_event_not_null", "transaction", type_="unique")
    op.drop_constraint("uq_transaction_player_id_idempotency_key_not_null", "transaction", type_="unique")

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
