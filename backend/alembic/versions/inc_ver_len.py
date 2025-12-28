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
    # Increase the length of version_num column in alembic_version table
    # Standard alembic uses VARCHAR(32), we need more for descriptive revision IDs
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=128),
        existing_nullable=False,
    )

def downgrade() -> None:
    # Revert back to 32 chars
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=128),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
