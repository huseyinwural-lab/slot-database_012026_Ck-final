"""reconciliation_findings table

Revision ID: 20251222_01_recon
Revises: 
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251222_01_recon"
down_revision = "abcd1234_ledgertables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reconciliation_findings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("player_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("tx_id", sa.String(length=64), nullable=True, index=True),
        sa.Column("provider_event_id", sa.String(length=128), nullable=True, index=True),
        sa.Column("provider_ref", sa.String(length=128), nullable=True, index=True),
        sa.Column("finding_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("severity", sa.String(length=16), nullable=False, index=True),
        sa.Column("status", sa.String(length=16), nullable=False, index=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_table("reconciliation_findings")
