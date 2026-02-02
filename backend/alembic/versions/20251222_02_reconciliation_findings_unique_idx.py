"""add unique index on reconciliation_findings

Revision ID: 20251222_02_reconciliation_findings_unique_idx
Revises: inc_ver_len
Create Date: 2025-12-22

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251222_02_reconciliation_findings_unique_idx"
down_revision = "inc_ver_len"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("reconciliation_findings") as batch_op:
        batch_op.create_unique_constraint(
            "uq_recon_provider_event_type",
            ["provider", "provider_event_id", "finding_type"],
        )


def downgrade() -> None:
    with op.batch_alter_table("reconciliation_findings") as batch_op:
        batch_op.drop_constraint(
            "uq_recon_provider_event_type",
            type_="unique",
        )
