"""add audit_event table

Revision ID: 7b01f4a2c9e1
Revises: 24e894ecb377
Create Date: 2025-12-17

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7b01f4a2c9e1"
down_revision = "24e894ecb377"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_audit_event_request_id"), "audit_event", ["request_id"], unique=False)
    op.create_index(op.f("ix_audit_event_actor_user_id"), "audit_event", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_event_tenant_id"), "audit_event", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_audit_event_action"), "audit_event", ["action"], unique=False)
    op.create_index(op.f("ix_audit_event_resource_type"), "audit_event", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_event_resource_id"), "audit_event", ["resource_id"], unique=False)
    op.create_index(op.f("ix_audit_event_result"), "audit_event", ["result"], unique=False)
    op.create_index(op.f("ix_audit_event_timestamp"), "audit_event", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_event_timestamp"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_result"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_resource_id"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_resource_type"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_action"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_tenant_id"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_actor_user_id"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_request_id"), table_name="audit_event")
    op.drop_table("audit_event")
