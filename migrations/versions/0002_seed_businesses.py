"""Seed the two business names LOOP currently issues quotations under.

Reference data, not user data: it ships with the schema so every environment
has the same business keys. Contact details are filled in later, from the real
quotation formats.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

BUSINESSES = (
    ("arcat_enterprises", "Arcat Enterprises"),
    ("arcat_automations", "Arcat Automations"),
)


def upgrade() -> None:
    businesses = sa.table(
        "businesses",
        sa.column("key", sa.String),
        sa.column("name", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        businesses,
        [{"key": key, "name": name, "is_active": True} for key, name in BUSINESSES],
    )


def downgrade() -> None:
    keys = ", ".join(f"'{key}'" for key, _ in BUSINESSES)
    op.execute(f"DELETE FROM businesses WHERE key IN ({keys})")
