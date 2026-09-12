"""Add a quantity to quotation lines.

Existing lines are backfilled with quantity 1, so every quotation already issued
keeps exactly the total it had before this migration.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quotation_items",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("quotation_items", "quantity")
