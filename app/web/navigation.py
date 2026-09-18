"""The links shown in the top bar.

One entry per link, exactly like the tiles in ``app/web/tools.py``. Adding,
removing, renaming or reordering top-bar links means editing this list only:
``base.html`` renders whatever it is handed and performs no role checks of its
own, so a new page never needs a template change to become reachable.
"""

from dataclasses import dataclass

from app.domain.enums import UserRole

EVERYONE = frozenset({UserRole.PROPRIETOR, UserRole.SERVICE_ENGINEER})
PROPRIETOR_ONLY = frozenset({UserRole.PROPRIETOR})


@dataclass(frozen=True)
class NavLink:
    label: str
    href: str
    #: Roles allowed to see the link. Visibility only — every page still
    #: enforces its own authorization in the route and the service.
    roles: frozenset[UserRole]
    #: True renders the link in the accent colour, as a call to action.
    emphasis: bool = False


NAV_LINKS: tuple[NavLink, ...] = (
    NavLink("Home", "/", EVERYONE),
    NavLink("Dashboard", "/dashboard", PROPRIETOR_ONLY),
    NavLink("Tasks", "/tasks", EVERYONE),
    NavLink("Customers", "/customers", PROPRIETOR_ONLY),
    NavLink("Quotations", "/quotations", PROPRIETOR_ONLY),
    NavLink("Invoices", "/invoices", PROPRIETOR_ONLY),
    NavLink("Inventory", "/inventory", EVERYONE),
    NavLink("+ New Task", "/tasks/new", PROPRIETOR_ONLY, emphasis=True),
)


def nav_for(role: UserRole) -> list[NavLink]:
    return [link for link in NAV_LINKS if role in link.roles]
