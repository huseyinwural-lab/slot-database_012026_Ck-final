"""add segment type to users

Revision ID: p1_segment_migration
Revises: previous_revision
Create Date: 2023-10-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'p1_segment_migration'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

# Define Enum type
segment_type_enum = postgresql.ENUM('INDIVIDUAL', 'DEALER', name='segment_type', create_type=False)

def upgrade():
    # Create Enum Type
    segment_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Add column as NULL first to prevent lock issues on large tables (though SQLite ignores this)
    # Postgres specific: Add column nullable, backfill, then alter to NOT NULL
    op.add_column('users', sa.Column('segment_type', sa.Enum('INDIVIDUAL', 'DEALER', name='segment_type'), nullable=True))
    
    # Backfill Data (Phase 2 of Migration Plan)
    op.execute("UPDATE users SET segment_type = 'INDIVIDUAL' WHERE segment_type IS NULL")
    
    # Set Not Null (Phase 3 of Migration Plan)
    op.alter_column('users', 'segment_type', nullable=False, server_default='INDIVIDUAL')

def downgrade():
    op.drop_column('users', 'segment_type')
    segment_type_enum.drop(op.get_bind(), checkfirst=True)
