"""Correct the business names: Arcat -> Arcot.

The two businesses were seeded in 0002 with a misspelt trading name. This
updates the existing rows in place (key and name) so quotations already issued
keep pointing at the same business row — no data is deleted or recreated.

Revision ID: 0003
Revises: 0002
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

#: (old key, new key, new display name)
RENAMES = (
    ("arcat_enterprises", "arcot_enterprises", "Arcot Enterprises"),
    ("arcat_automations", "arcot_automations", "Arcot Automations"),
)


def _apply(pairs) -> None:
    for old_key, new_key, new_name in pairs:
        op.execute(
            "UPDATE businesses "
            f"SET key = '{new_key}', name = '{new_name}' "
            f"WHERE key = '{old_key}'"
        )


def upgrade() -> None:
    _apply(RENAMES)


def downgrade() -> None:
    _apply(
        (new_key, old_key, old_name)
        for old_key, new_key, old_name in (
            ("arcat_enterprises", "arcot_enterprises", "Arcat Enterprises"),
            ("arcat_automations", "arcot_automations", "Arcat Automations"),
        )
    )
