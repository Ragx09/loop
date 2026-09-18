"""Customers, equipment, inventory, invoicing and service reports.

Purely additive: no existing column is dropped or renamed, and the two columns
added to ``tasks`` are nullable, so every task, quotation and user created
before this migration keeps working untouched.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

INVOICE_STATUS = sa.Enum(
    "PENDING",
    "PARTIALLY_PAID",
    "PAID",
    "OVERDUE",
    name="invoice_status",
)
PAYMENT_METHOD = sa.Enum(
    "CASH",
    "BANK_TRANSFER",
    "UPI",
    "CHEQUE",
    "CARD",
    name="payment_method",
)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    INVOICE_STATUS.create(bind, checkfirst=True)
    PAYMENT_METHOD.create(bind, checkfirst=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(60), nullable=True),
        sa.Column("email", sa.String(160), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("gstin", sa.String(32), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index("ix_customers_name", "customers", ["name"])

    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("serial_number", sa.String(120), nullable=True),
        sa.Column("installed_at", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_equipment_customer_id", "equipment", ["customer_id"])

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(80), nullable=True),
        sa.Column("hsn_code", sa.String(32), nullable=True),
        sa.Column("purchase_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("selling_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("stock_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index("ix_inventory_items_sku", "inventory_items", ["sku"], unique=True)
    op.create_index("ix_inventory_items_name", "inventory_items", ["name"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_number", sa.String(60), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "business_id",
            sa.Integer(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "quotation_id",
            sa.Integer(),
            sa.ForeignKey("quotations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", INVOICE_STATUS, nullable=False, server_default="PENDING"),
        sa.Column("is_interstate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *_timestamps(),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_business_id", "invoices", ["business_id"])
    op.create_index("ix_invoices_customer_id", "invoices", ["customer_id"])
    op.create_index("ix_invoices_quotation_id", "invoices", ["quotation_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_created_by_id", "invoices", ["created_by_id"])

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("particulars", sa.String(500), nullable=False),
        sa.Column("hsn_code", sa.String(32), nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("method", PAYMENT_METHOD, nullable=False),
        sa.Column("paid_at", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(120), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])

    op.create_table(
        "materials_used",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "inventory_item_id",
            sa.Integer(),
            sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_materials_used_task_id", "materials_used", ["task_id"])
    op.create_index(
        "ix_materials_used_inventory_item_id", "materials_used", ["inventory_item_id"]
    )

    op.create_table(
        "service_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("work_performed", sa.String(2000), nullable=False),
        sa.Column("meter_reading", sa.String(60), nullable=True),
        sa.Column("customer_signature", sa.String(160), nullable=True),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *_timestamps(),
    )
    op.create_index("ix_service_reports_task_id", "service_reports", ["task_id"], unique=True)
    op.create_index("ix_service_reports_created_by_id", "service_reports", ["created_by_id"])

    # Nullable, so existing rows need no backfill and keep their free-text
    # customer_name exactly as it was.
    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("customer_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("equipment_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_tasks_customer_id", "customers", ["customer_id"], ["id"], ondelete="SET NULL"
        )
        batch.create_foreign_key(
            "fk_tasks_equipment_id", "equipment", ["equipment_id"], ["id"], ondelete="SET NULL"
        )
    op.create_index("ix_tasks_customer_id", "tasks", ["customer_id"])
    op.create_index("ix_tasks_equipment_id", "tasks", ["equipment_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_equipment_id", table_name="tasks")
    op.drop_index("ix_tasks_customer_id", table_name="tasks")
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("fk_tasks_equipment_id", type_="foreignkey")
        batch.drop_constraint("fk_tasks_customer_id", type_="foreignkey")
        batch.drop_column("equipment_id")
        batch.drop_column("customer_id")

    op.drop_table("service_reports")
    op.drop_table("materials_used")
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("inventory_items")
    op.drop_table("equipment")
    op.drop_table("customers")

    bind = op.get_bind()
    PAYMENT_METHOD.drop(bind, checkfirst=True)
    INVOICE_STATUS.drop(bind, checkfirst=True)
