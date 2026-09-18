"""The personas offered on the sign-in page.

One entry per demo account, in the same shape as the top-bar links in
``app/web/navigation.py`` and the launcher tiles in ``app/web/tools.py``:
configuration as data, so adding a persona means editing this list only. The
template renders whatever it is handed and makes no decisions of its own.
"""

from dataclasses import dataclass

from app.config import get_settings
from app.domain.enums import UserRole


@dataclass(frozen=True)
class DemoAccount:
    #: Value posted by the sign-in form. Stable: it is part of the URL contract.
    key: str
    #: Username of the seeded user this persona signs in as.
    username: str
    full_name: str
    role: UserRole
    #: Button wording.
    label: str
    #: One line under the button, describing what this persona can do.
    description: str


DEMO_ACCOUNTS: tuple[DemoAccount, ...] = (
    DemoAccount(
        key="proprietor",
        username="demo.owner",
        full_name="Demo Proprietor",
        role=UserRole.PROPRIETOR,
        label="Explore as Proprietor",
        description="Create and assign tasks, build quotations, download PDFs.",
    ),
    DemoAccount(
        key="engineer",
        username="demo.ravi",
        full_name="Ravi Kumar",
        role=UserRole.SERVICE_ENGINEER,
        label="Explore as Service Engineer",
        description="The field view: my jobs, fill in details, progress, complete.",
    ),
)

#: Seeded alongside the personas so task assignment has more than one engineer
#: to choose from. Not offered as a sign-in option.
DEMO_EXTRA_ENGINEERS: tuple[tuple[str, str], ...] = (
    ("demo.anita", "Anita Sharma"),
)


def demo_accounts() -> tuple[DemoAccount, ...]:
    """The personas to offer, or nothing at all when demo mode is off."""
    return DEMO_ACCOUNTS if get_settings().demo_mode else ()


def get_demo_account(key: str) -> DemoAccount | None:
    for account in DEMO_ACCOUNTS:
        if account.key == key:
            return account
    return None
