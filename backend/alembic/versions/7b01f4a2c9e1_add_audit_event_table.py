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
        "auditevent",
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

    op.create_index(op.f("ix_auditevent_request_id"), "auditevent", ["request_id"], unique=False)
    op.create_index(op.f("ix_auditevent_actor_user_id"), "auditevent", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_auditevent_tenant_id"), "auditevent", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_auditevent_action"), "auditevent", ["action"], unique=False)
    op.create_index(op.f("ix_auditevent_resource_type"), "auditevent", ["resource_type"], unique=False)
    op.create_index(op.f("ix_auditevent_resource_id"), "auditevent", ["resource_id"], unique=False)
    op.create_index(op.f("ix_auditevent_result"), "auditevent", ["result"], unique=False)
    op.create_index(op.f("ix_auditevent_timestamp"), "auditevent", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auditevent_timestamp"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_result"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_resource_id"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_resource_type"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_action"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_tenant_id"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_actor_user_id"), table_name="auditevent")
    op.drop_index(op.f("ix_auditevent_request_id"), table_name="auditevent")
    op.drop_table("auditevent")
