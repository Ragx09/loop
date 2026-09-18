"""The tools shown on the LOOP home page.

Each tool is one entry here. Adding a future tool (reports, inventory, …) means
appending one ``Tool`` — the home page, its layout and its role filtering all
follow automatically, with no template change.
"""

from dataclasses import dataclass

from app.domain.enums import UserRole


@dataclass(frozen=True)
class Tool:
    key: str
    name: str
    description: str
    href: str
    #: Inline SVG path data drawn in the tool tile.
    icon: str
    roles: frozenset[UserRole]


_TASKS_ICON = "M4 6h16M4 12h16M4 18h10"
_QUOTATION_ICON = "M6 3h9l5 5v13H6zM15 3v5h5M9 13h7M9 17h7"
_CUSTOMER_ICON = "M16 19v-2a4 4 0 00-8 0v2M12 11a4 4 0 100-8 4 4 0 000 8"
_INVOICE_ICON = "M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6"
_PAYMENT_ICON = "M3 7h18v10H3zM3 11h18M7 15h3"
_INVENTORY_ICON = "M4 8l8-4 8 4v8l-8 4-8-4zM4 8l8 4 8-4M12 12v8"
_DASHBOARD_ICON = "M4 20V10M10 20V4M16 20v-7M22 20H2"

TOOLS: tuple[Tool, ...] = (
    Tool(
        key="tasks",
        name="Tasks",
        description="Create service calls and material despatches, assign them and track status.",
        href="/tasks",
        icon=_TASKS_ICON,
        roles=frozenset({UserRole.PROPRIETOR, UserRole.SERVICE_ENGINEER}),
    ),
    Tool(
        key="dashboard",
        name="Dashboard",
        description="Revenue, outstanding money, job counts and monthly trends at a glance.",
        href="/dashboard",
        icon=_DASHBOARD_ICON,
        roles=frozenset({UserRole.PROPRIETOR}),
    ),
    Tool(
        key="customers",
        name="Customers",
        description="Customer records, their equipment, and the full history of work done.",
        href="/customers",
        icon=_CUSTOMER_ICON,
        roles=frozenset({UserRole.PROPRIETOR}),
    ),
    Tool(
        key="quotations",
        name="Generate Quotation",
        description="Build a quotation under any business name and download it as a PDF.",
        href="/quotations/new",
        icon=_QUOTATION_ICON,
        roles=frozenset({UserRole.PROPRIETOR}),
    ),
    Tool(
        key="invoices",
        name="Invoices",
        description="Raise invoices with a GST breakdown, or convert an accepted quotation.",
        href="/invoices",
        icon=_INVOICE_ICON,
        roles=frozenset({UserRole.PROPRIETOR}),
    ),
    Tool(
        key="payments",
        name="Payments",
        description="Record what has been collected and see what is still outstanding.",
        href="/invoices/payments",
        icon=_PAYMENT_ICON,
        roles=frozenset({UserRole.PROPRIETOR}),
    ),
    Tool(
        key="inventory",
        name="Inventory",
        description="Stock levels, minimum-stock warnings and the parts used on jobs.",
        href="/inventory",
        icon=_INVENTORY_ICON,
        roles=frozenset({UserRole.PROPRIETOR, UserRole.SERVICE_ENGINEER}),
    ),
)


def tools_for(role: UserRole) -> list[Tool]:
    return [tool for tool in TOOLS if role in tool.roles]
