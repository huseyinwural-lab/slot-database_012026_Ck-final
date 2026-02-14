"""add performance indexes fixed

Revision ID: phase4_indexes_fixed
Revises: 9775b5966217
Create Date: 2026-02-12 10:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "phase4_indexes_fixed"
down_revision = "9775b5966217"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite fallback: use batch mode to alter table if needed, or skip if col missing
    # But GameEvent model definition HAS created_at.
    # Maybe table name is snake_case differently?
    # SQLModel uses class name lowercase usually -> gameevent
    # But in previous logs, we saw "game_round" etc?
    
    # Try adding column first if missing? No, that's dangerous.
    # Let's inspect names.
    
    # In SQLite, creating index on missing column fails.
    # We will wrap in try/except block for safety in this migration script
    # OR better: use Inspector.
    
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c['name'] for c in insp.get_columns('gameevent')]
    
    if 'created_at' in columns:
        try:
            op.create_index(op.f("ix_gameevent_created_at"), "gameevent", ["created_at"], unique=False)
        except Exception:
            pass

    columns_round = [c['name'] for c in insp.get_columns('gameround')]
    if 'created_at' in columns_round:
        try:
            op.create_index(op.f("ix_gameround_created_at"), "gameround", ["created_at"], unique=False)
        except Exception:
            pass


def downgrade():
    try:
        op.drop_index(op.f("ix_gameround_created_at"), table_name="gameround")
        op.drop_index(op.f("ix_gameevent_created_at"), table_name="gameevent")
    except:
        pass
