"""affiliate p0 models

Revision ID: bc11f2c6a3aa
Revises: a8e7c2f57494
Create Date: 2026-01-18

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bc11f2c6a3aa"
down_revision = "a8e7c2f57494"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- affiliate: partner ---
    with op.batch_alter_table("affiliate") as batch:
        batch.add_column(sa.Column("code", sa.String(), nullable=True))
        batch.create_unique_constraint("uq_affiliate_tenant_email", ["tenant_id", "email"])
        batch.create_unique_constraint("uq_affiliate_tenant_code", ["tenant_id", "code"])

    # --- affiliate: tracking link extension ---
    with op.batch_alter_table("affiliatelink") as batch:
        batch.add_column(sa.Column("offer_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("landing_path", sa.String(), nullable=True, server_default="/"))
        batch.add_column(sa.Column("currency", sa.String(), nullable=True))
        batch.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))

    # --- offers ---
    op.create_table(
        "affiliateoffer",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),  # cpa | revshare
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("cpa_amount", sa.Float(), nullable=True),
        sa.Column("min_deposit", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_affiliateoffer_tenant_name"),
    )

    # --- affiliate ledger ---
    op.create_table(
        "affiliateledger",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("partner_id", sa.String(), nullable=False, index=True),
        sa.Column("offer_id", sa.String(), nullable=True, index=True),
        sa.Column("player_id", sa.String(), nullable=True, index=True),
        sa.Column("entry_type", sa.String(), nullable=False),  # accrual|payout|adjustment
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # --- payouts ---
    op.create_table(
        "affiliatepayout",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("partner_id", sa.String(), nullable=False, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "reference", name="uq_affiliatepayout_tenant_reference"),
    )

    # --- creatives ---
    op.create_table(
        "affiliatecreative",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("size", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("affiliatecreative")
    op.drop_table("affiliatepayout")
    op.drop_table("affiliateledger")
    op.drop_table("affiliateoffer")

    with op.batch_alter_table("affiliatelink") as batch:
        batch.drop_column("expires_at")
        batch.drop_column("currency")
        batch.drop_column("landing_path")
        batch.drop_column("offer_id")

    with op.batch_alter_table("affiliate") as batch:
        batch.drop_constraint("uq_affiliate_tenant_code", type_="unique")
        batch.drop_constraint("uq_affiliate_tenant_email", type_="unique")
        batch.drop_column("code")
