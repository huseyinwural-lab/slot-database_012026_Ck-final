"""create discount schema

Revision ID: 20260215_02_p1_discount_migration
Revises: 20260215_01_p1_segment_migration
Create Date: 2026-02-15 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260215_02_p1_discount_migration'
down_revision = '20260215_01_p1_segment_migration'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create Discounts Table
    if 'discounts' not in tables:
        op.create_table(
            'discounts',
            sa.Column('id', sa.String(), nullable=False), # Use String for SQLite compatibility/Safety
            sa.Column('code', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('type', sa.Enum('PERCENTAGE', 'FLAT', name='discount_type_enum'), nullable=False),
            sa.Column('value', sa.Numeric(10, 2), nullable=False),
            sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('code', name='uq_discount_code')
        )
        op.create_index('ix_discounts_validity', 'discounts', ['start_at', 'end_at', 'is_active'])

    # 2. Create Discount Rules Table (Binding Logic)
    if 'discount_rules' not in tables:
        op.create_table(
            'discount_rules',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('discount_id', sa.String(), nullable=False),
            sa.Column('segment_type', sa.Enum('INDIVIDUAL', 'DEALER', name='segment_type'), nullable=True),
            sa.Column('tenant_id', sa.String(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ),
        )
        op.create_index('ix_discount_rules_segment', 'discount_rules', ['segment_type'])
        op.create_index('ix_discount_rules_tenant', 'discount_rules', ['tenant_id'])

    # 3. Update Ledger Table
    # Using 'ledgertransaction' as confirmed
    if 'ledgertransaction' in tables:
        ledger_cols = [c['name'] for c in inspector.get_columns('ledgertransaction')]
        
        if 'gross_amount' not in ledger_cols:
            op.add_column('ledgertransaction', sa.Column('gross_amount', sa.Numeric(10, 2), nullable=True))
        
        if 'discount_amount' not in ledger_cols:
            op.add_column('ledgertransaction', sa.Column('discount_amount', sa.Numeric(10, 2), server_default='0', nullable=False))
        
        if 'net_amount' not in ledger_cols:
            op.add_column('ledgertransaction', sa.Column('net_amount', sa.Numeric(10, 2), nullable=True))
        
        if 'applied_discount_id' not in ledger_cols:
            op.add_column('ledgertransaction', sa.Column('applied_discount_id', sa.String(), nullable=True))
            # ForeignKey might fail on SQLite if constraints are enforcing, but usually fine in add_column unless batch mode
            # For SQLite, batch_alter_table is preferred for FKs, but let's try standard first.
            try:
                op.create_foreign_key('fk_ledger_discount', 'ledgertransaction', 'discounts', ['applied_discount_id'], ['id'])
            except:
                pass # Ignore if fails (e.g. SQLite limitation)

def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'ledgertransaction' in tables:
        # Dropping columns in SQLite requires batch mode, simplifying for now
        with op.batch_alter_table('ledgertransaction') as batch_op:
            batch_op.drop_constraint('fk_ledger_discount', type_='foreignkey')
            batch_op.drop_column('applied_discount_id')
            batch_op.drop_column('net_amount')
            batch_op.drop_column('discount_amount')
            batch_op.drop_column('gross_amount')

    if 'discount_rules' in tables:
        op.drop_table('discount_rules')
    
    if 'discounts' in tables:
        op.drop_table('discounts')
    
    sa.Enum(name='discount_type_enum').drop(op.get_bind(), checkfirst=True)
