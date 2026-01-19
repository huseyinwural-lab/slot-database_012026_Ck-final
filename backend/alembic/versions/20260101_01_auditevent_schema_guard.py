"""P0: AuditEvent schema guard (add missing columns)

Revision ID: 20260101_01
Revises: 20251231_02
Create Date: 2026-01-01

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260101_01"
down_revision = "20251231_02"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()

    if bind.dialect.name == "sqlite":
        cols = [row[1] for row in bind.execute(sa.text(f"PRAGMA table_info({table_name})")).fetchall()]
        return column_name in cols

    res = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :t
              AND column_name = :c
            LIMIT 1
            """
        ),
        {"t": table_name, "c": column_name},
    ).fetchone()
    return res is not None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # Core fields
    if not _column_exists("auditevent", "status"):
        op.add_column("auditevent", sa.Column("status", sa.String(), nullable=True))
    if not _column_exists("auditevent", "reason"):
        op.add_column("auditevent", sa.Column("reason", sa.String(), nullable=True))

    # Payload fields expected by code/schema
    # On SQLite, JSONB is not available; use TEXT.
    json_type = sa.Text() if is_sqlite else sa.dialects.postgresql.JSONB()

    if not _column_exists("auditevent", "before_json"):
        op.add_column("auditevent", sa.Column("before_json", json_type, nullable=True))
    if not _column_exists("auditevent", "after_json"):
        op.add_column("auditevent", sa.Column("after_json", json_type, nullable=True))
    if not _column_exists("auditevent", "diff_json"):
        op.add_column("auditevent", sa.Column("diff_json", json_type, nullable=True))
    if not _column_exists("auditevent", "metadata_json"):
        op.add_column("auditevent", sa.Column("metadata_json", json_type, nullable=True))

    # Error fields
    if not _column_exists("auditevent", "error_code"):
        op.add_column("auditevent", sa.Column("error_code", sa.String(), nullable=True))
    if not _column_exists("auditevent", "error_message"):
        op.add_column("auditevent", sa.Column("error_message", sa.String(), nullable=True))

    # Hash chain fields
    if not _column_exists("auditevent", "row_hash"):
        op.add_column("auditevent", sa.Column("row_hash", sa.String(), nullable=True))
    if not _column_exists("auditevent", "prev_row_hash"):
        op.add_column("auditevent", sa.Column("prev_row_hash", sa.String(), nullable=True))
    if not _column_exists("auditevent", "chain_id"):
        op.add_column("auditevent", sa.Column("chain_id", sa.String(), nullable=True))
    if not _column_exists("auditevent", "sequence"):
        op.add_column("auditevent", sa.Column("sequence", sa.Integer(), nullable=True))


def downgrade() -> None:
    # Intentionally no-op (prod-safe)
    pass
