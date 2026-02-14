"""Risk Profile (canonical risk_profiles + safe enum)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers
revision = '20260216_01_risk_profile'
down_revision = '20260215_02_p1_discount_migration'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    tables = inspector.get_table_names()

    # --- BRIDGE: rename risk_profile -> risk_profiles ---
    if 'risk_profile' in tables and 'risk_profiles' not in tables:
        op.rename_table('risk_profile', 'risk_profiles')

    tables = inspector.get_table_names()

    # --- CREATE ENUM (once) ---
    risk_enum = postgresql.ENUM(
        'LOW',
        'MEDIUM',
        'HIGH',
        name='risklevel'
    )
    risk_enum.create(bind, checkfirst=True)

    # --- CREATE TABLE IF NOT EXISTS ---
    if 'risk_profiles' not in tables:
        op.create_table(
            'risk_profiles',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('player_id', sa.Integer, nullable=False),
            sa.Column(
                'risk_level',
                postgresql.ENUM(
                    name='risklevel',
                    create_type=False
                ),
                server_default='LOW',
                nullable=True
            ),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'risk_profiles' in inspector.get_table_names():
        op.drop_table('risk_profiles')

    risk_enum = postgresql.ENUM(name='risklevel')
    risk_enum.drop(bind, checkfirst=True)
