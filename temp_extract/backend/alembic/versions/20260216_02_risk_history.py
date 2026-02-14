"""create risk history schema

Revision ID: 20260216_02_risk_history
Revises: 20260216_01_risk_profile
Create Date: 2026-02-16 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "20260216_02_risk_history"
down_revision = "20260216_01_risk_profile"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "risk_history" not in tables:
        op.create_table(
            "risk_history",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("old_score", sa.Integer(), nullable=False),
            sa.Column("new_score", sa.Integer(), nullable=False),
            sa.Column("old_level", sa.String(), nullable=False),
            sa.Column("new_level", sa.String(), nullable=False),
            sa.Column("change_reason", sa.String(), nullable=False),
            sa.Column("changed_by", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_risk_history_user_id", "risk_history", ["user_id"])
        op.create_index("ix_risk_history_tenant_id", "risk_history", ["tenant_id"])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "risk_history" in tables:
        try:
            op.drop_index("ix_risk_history_tenant_id", table_name="risk_history")
        except Exception:
            pass
        try:
            op.drop_index("ix_risk_history_user_id", table_name="risk_history")
        except Exception:
            pass
        op.drop_table("risk_history")
