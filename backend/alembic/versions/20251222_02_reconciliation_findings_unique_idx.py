"""add unique index on reconciliation_findings

Revision ID: 20251222_02_reconciliation_findings_unique_idx
Revises: 20251222_01_reconciliation_findings
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251222_02_reconciliation_findings_unique_idx"
down_revision = "20251222_01_reconciliation_findings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_recon_provider_event_type",
        "reconciliation_findings",
        ["provider", "provider_event_id", "finding_type"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_recon_provider_event_type",
        "reconciliation_findings",
        type_="unique",
    )
