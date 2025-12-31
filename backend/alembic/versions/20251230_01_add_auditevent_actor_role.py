"""add auditevent.actor_role

P0: Fix login 500 caused by schema drift (backend selects auditevent.actor_role but
column missing in DB).

Revision ID: 20251230_01
Revises: c553520d78cd
Create Date: 2025-12-30

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251230_01"
down_revision = "c553520d78cd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable first-pass to unblock runtime; can be tightened later.
    with op.batch_alter_table("auditevent") as batch_op:
        batch_op.add_column(sa.Column("actor_role", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("auditevent") as batch_op:
        batch_op.drop_column("actor_role")
