"""payout_attempts table

Revision ID: 20251223_01_payout_attempts
Revises: 3acefa8a3e7d
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251223_01_payout_attempts"
down_revision: Union[str, None] = "3acefa8a3e7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if not bind.dialect.has_table(bind, "payoutattempt"):
        op.create_table(
            "payoutattempt",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("withdraw_tx_id", sa.String(length=36), nullable=False, index=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=False, index=True),
            sa.Column("provider", sa.String(length=64), nullable=False, index=True),
            sa.Column("provider_event_id", sa.String(length=128), nullable=True, index=True),
            sa.Column("idempotency_key", sa.String(length=128), nullable=True, index=True),
            sa.Column("status", sa.String(length=32), nullable=False, index=True),
            sa.Column("error_code", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["withdraw_tx_id"], ["transaction.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        )

    # SQLite does not support ALTER TABLE ADD CONSTRAINT. In dev we rely on
    # application-level idempotency checks and keep the schema simple. In
    # Postgres, ops can enforce these via partial unique indexes.
    if dialect == "sqlite":
        return

    # For Postgres or other real DBs, create the same uniques. In a production
    # environment these can be evolved into partial indexes.
    op.create_unique_constraint(
        "uq_payoutattempt_provider_event",
        "payoutattempt",
        ["provider", "provider_event_id"],
    )
    op.create_unique_constraint(
        "uq_payoutattempt_withdraw_idem",
        "payoutattempt",
        ["withdraw_tx_id", "idempotency_key"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.drop_constraint(
            "uq_payoutattempt_withdraw_idem", "payoutattempt", type_="unique"
        )
        op.drop_constraint(
            "uq_payoutattempt_provider_event", "payoutattempt", type_="unique"
        )

    op.drop_table("payoutattempt")
