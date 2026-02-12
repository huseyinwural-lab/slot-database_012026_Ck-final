"""create discount schema

Revision ID: p1_discount_migration
Revises: p1_segment_migration
Create Date: 2023-10-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'p1_discount_migration'
down_revision = 'phase4_real_final_v56'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create Discounts Table
    op.create_table(
        'discounts',
        sa.Column('id', sa.UUID(), nullable=False),
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

    # 2. Create Discount Rules Table (Binding Logic)
    op.create_table(
        'discount_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('discount_id', sa.UUID(), nullable=False),
        sa.Column('segment_type', sa.Enum('INDIVIDUAL', 'DEALER', name='segment_type'), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['discount_id'], ['discounts.id'], ),
    )
    
    # Indexes for performance
    op.create_index('ix_discount_rules_segment', 'discount_rules', ['segment_type'])
    op.create_index('ix_discount_rules_tenant', 'discount_rules', ['tenant_id'])
    op.create_index('ix_discounts_validity', 'discounts', ['start_at', 'end_at', 'is_active'])

    # 3. Update Ledger Table for Reporting (NGR)
    op.add_column('pricing_ledger', sa.Column('gross_amount', sa.Numeric(10, 2), nullable=True))
    op.add_column('pricing_ledger', sa.Column('discount_amount', sa.Numeric(10, 2), server_default='0', nullable=False))
    # net_amount is effectively the existing 'amount' column, but we might rename or alias it in views.
    op.add_column('pricing_ledger', sa.Column('applied_discount_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_ledger_discount', 'pricing_ledger', 'discounts', ['applied_discount_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_ledger_discount', 'pricing_ledger', type_='foreignkey')
    op.drop_column('pricing_ledger', 'applied_discount_id')
    op.drop_column('pricing_ledger', 'discount_amount')
    op.drop_column('pricing_ledger', 'gross_amount')
    op.drop_table('discount_rules')
    op.drop_table('discounts')
    sa.Enum(name='discount_type_enum').drop(op.get_bind(), checkfirst=True)
