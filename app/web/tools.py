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
        key="quotations",
        name="Generate Quotation",
        description="Build a quotation under any business name and download it as a PDF.",
        href="/quotations/new",
        icon=_QUOTATION_ICON,
        roles=frozenset({UserRole.PROPRIETOR}),
    ),
)


def tools_for(role: UserRole) -> list[Tool]:
    return [tool for tool in TOOLS if role in tool.roles]
