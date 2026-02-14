"""Risk Versioning (guarded, canonical table only)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = '20260216_03_risk_versioning'
down_revision = '20260216_02_risk_history'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'risk_profiles' not in inspector.get_table_names():
        return

    columns = [c['name'] for c in inspector.get_columns('risk_profiles')]

    if 'version' not in columns:
        op.add_column(
            'risk_profiles',
            sa.Column('version', sa.Integer, server_default='1', nullable=False)
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'risk_profiles' not in inspector.get_table_names():
        return

    columns = [c['name'] for c in inspector.get_columns('risk_profiles')]

    if 'version' in columns:
        op.drop_column('risk_profiles', 'version')
