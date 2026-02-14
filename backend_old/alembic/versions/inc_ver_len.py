"""increase alembic version length

Revision ID: inc_ver_len
Revises: 20251222_01_recon
Create Date: 2025-12-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'inc_ver_len'
down_revision = '20251222_01_recon'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("alembic_version") as batch_op:
        batch_op.alter_column(
            "version_num",
            existing_type=sa.String(length=32),
            type_=sa.String(length=128),
            existing_nullable=False,
        )

def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("alembic_version") as batch_op:
        batch_op.alter_column(
            "version_num",
            existing_type=sa.String(length=128),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
