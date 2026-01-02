"""P0: AuditEvent schema guard (add missing columns)

Revision ID: 20260101_01
Revises: 20251231_02
Create Date: 2026-01-01

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260101_01"
down_revision = "20251231_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Core fields added after initial audit table migration
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS status VARCHAR NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS reason VARCHAR NULL;")

    # Payload fields expected by code/schema
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS before_json JSONB NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS after_json JSONB NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS diff_json JSONB NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS metadata_json JSONB NULL;")

    # Error fields
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS error_code VARCHAR NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS error_message VARCHAR NULL;")

    # Hash chain fields used by audit service queries
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS row_hash VARCHAR NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS prev_row_hash VARCHAR NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS chain_id VARCHAR NULL;")
    op.execute("ALTER TABLE auditevent ADD COLUMN IF NOT EXISTS sequence INTEGER NULL;")


def downgrade() -> None:
    # Intentionally no-op (prod-safe)
    pass
