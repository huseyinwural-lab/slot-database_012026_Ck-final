"""create discount schema

Revision ID: 20260215_02_p1_discount_migration
Revises: 20260215_01_p1_segment_migration
Create Date: 2026-02-15 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260215_02_p1_discount_migration"
down_revision = "20260215_01_p1_segment_migration"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # REUSE ONLY: segment_type (created in 20260215_01) -> do NOT recreate DB type
    segment_type_enum = postgresql.ENUM(
        "INDIVIDUAL",
        "DEALER",
        name="segment_type",
        create_type=False,
    )

    # CREATE ONCE: discount_type_enum
    discount_type_enum = postgresql.ENUM(
        "PERCENTAGE",
        "FLAT",
        name="discount_type_enum",
    )
    discount_type_enum.create(bind, checkfirst=True)

    # readonly handle (no create on table create hook)
    discount_type_enum_ro = postgresql.ENUM(
        "PERCENTAGE",
        "FLAT",
        name="discount_type_enum",
        create_type=False,
    )

    # 1) discounts
    if "discounts" not in tables:
        op.create_table(
            "discounts",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("type", discount_type_enum_ro, nullable=False),
            sa.Column("value", sa.Numeric(10, 2), nullable=False),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_discount_code"),
        )
        op.create_index("ix_discounts_validity", "discounts", ["start_at", "end_at", "is_active"])

    # 2) discount_rules
    if "discount_rules" not in tables:
        op.create_table(
            "discount_rules",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("discount_id", sa.String(), nullable=False),
            sa.Column("segment_type", segment_type_enum, nullable=True),
            sa.Column("tenant_id", sa.String(), nullable=True),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["discount_id"], ["discounts.id"]),
        )
        op.create_index("ix_discount_rules_segment", "discount_rules", ["segment_type"])
        op.create_index("ix_discount_rules_tenant", "discount_rules", ["tenant_id"])

    # 3) ledgertransaction updates
    if "ledgertransaction" in tables:
        ledger_cols = [c["name"] for c in inspector.get_columns("ledgertransaction")]

        if "gross_amount" not in ledger_cols:
            op.add_column("ledgertransaction", sa.Column("gross_amount", sa.Numeric(10, 2), nullable=True))

        if "discount_amount" not in ledger_cols:
            op.add_column(
                "ledgertransaction",
                sa.Column("discount_amount", sa.Numeric(10, 2), server_default="0", nullable=False),
            )

        if "net_amount" not in ledger_cols:
            op.add_column("ledgertransaction", sa.Column("net_amount", sa.Numeric(10, 2), nullable=True))

        if "applied_discount_id" not in ledger_cols:
            op.add_column("ledgertransaction", sa.Column("applied_discount_id", sa.String(), nullable=True))
            try:
                op.create_foreign_key(
                    "fk_ledger_discount",
                    "ledgertransaction",
                    "discounts",
                    ["applied_discount_id"],
                    ["id"],
                )
            except Exception:
                pass


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "ledgertransaction" in tables:
        with op.batch_alter_table("ledgertransaction") as batch_op:
            try:
                batch_op.drop_constraint("fk_ledger_discount", type_="foreignkey")
            except Exception:
                pass

            for col in ["applied_discount_id", "net_amount", "discount_amount", "gross_amount"]:
                try:
                    batch_op.drop_column(col)
                except Exception:
                    pass

    if "discount_rules" in tables:
        op.drop_table("discount_rules")

    if "discounts" in tables:
        op.drop_table("discounts")

    # drop only discount_type_enum (segment_type is owned by previous migration)
    postgresql.ENUM(name="discount_type_enum").drop(bind, checkfirst=True)
