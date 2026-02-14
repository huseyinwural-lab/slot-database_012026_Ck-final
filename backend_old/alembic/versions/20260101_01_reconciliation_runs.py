"""reconciliation_runs table

Revision ID: 20260101_01_reconciliation_runs
Revises: 20251222_02_reconciliation_findings_unique_idx
Create Date: 2026-01-01

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260101_01_reconciliation_runs"
down_revision = "20251222_02_reconciliation_findings_unique_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reconciliation_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False, index=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("stats_json", sa.JSON(), nullable=True),
        sa.Column("error_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # Partial unique index for idempotency_key when not null
    op.create_index(
        "ux_recon_runs_provider_idempotency_key_not_null",
        "reconciliation_runs",
        ["provider", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # Operational indexes
    op.create_index(
        "ix_recon_runs_provider_created_at",
        "reconciliation_runs",
        ["provider", "created_at"],
    )
    op.create_index(
        "ix_recon_runs_provider_window",
        "reconciliation_runs",
        ["provider", "window_start", "window_end"],
    )


def downgrade() -> None:
    op.drop_index("ix_recon_runs_provider_window", table_name="reconciliation_runs")
    op.drop_index("ix_recon_runs_provider_created_at", table_name="reconciliation_runs")
    op.drop_index(
        "ux_recon_runs_provider_idempotency_key_not_null",
        table_name="reconciliation_runs",
    )
    op.drop_table("reconciliation_runs")
