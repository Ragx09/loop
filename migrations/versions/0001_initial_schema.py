"""Initial LOOP schema: users, tasks, businesses, quotations.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

user_role = sa.Enum("PROPRIETOR", "SERVICE_ENGINEER", name="user_role")
task_type = sa.Enum("SERVICE_CALL", "SEND_MATERIAL", name="task_type")
task_status = sa.Enum(
    "YET_TO_ASSIGN", "ASSIGNED", "IN_PROGRESS", "COMPLETED", name="task_status"
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_type", task_type, nullable=False),
        sa.Column("status", task_status, nullable=False, server_default="YET_TO_ASSIGN"),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("customer_name", sa.String(160), nullable=True),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("meter_reading", sa.String(60), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("assigned_engineer_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["assigned_engineer_id"],
            ["users.id"],
            name="fk_tasks_engineer",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="fk_tasks_created_by", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_scheduled_date", "tasks", ["scheduled_date"])
    op.create_index("ix_tasks_assigned_engineer_id", "tasks", ["assigned_engineer_id"])
    op.create_index("ix_tasks_created_by_id", "tasks", ["created_by_id"])
    op.create_index("ix_tasks_status_scheduled_date", "tasks", ["status", "scheduled_date"])

    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(60), nullable=True),
        sa.Column("email", sa.String(160), nullable=True),
        sa.Column("gstin", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("key", name="uq_businesses_key"),
    )
    op.create_index("ix_businesses_key", "businesses", ["key"])

    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quotation_number", sa.String(60), nullable=False),
        sa.Column("quotation_date", sa.Date(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("template_key", sa.String(64), nullable=False),
        sa.Column("customer_name", sa.String(160), nullable=False),
        sa.Column("customer_address", sa.String(500), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name="fk_quotations_business",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_quotations_created_by",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_quotations_number", "quotations", ["quotation_number"])
    op.create_index("ix_quotations_business_id", "quotations", ["business_id"])
    op.create_index("ix_quotations_created_by_id", "quotations", ["created_by_id"])

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("particulars", sa.String(500), nullable=False),
        sa.Column("hsn_code", sa.String(32), nullable=True),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["quotation_id"],
            ["quotations.id"],
            name="fk_quotation_items_quotation",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_quotation_items_quotation_id", "quotation_items", ["quotation_id"])


def downgrade() -> None:
    op.drop_table("quotation_items")
    op.drop_table("quotations")
    op.drop_table("businesses")
    op.drop_table("tasks")
    op.drop_table("users")
    task_status.drop(op.get_bind(), checkfirst=True)
    task_type.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
