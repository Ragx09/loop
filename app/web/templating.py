"""Jinja environment for the application UI (separate from quotation formats).

Everything registered here is available in every page template, which is why
wording, navigation and formatting can be changed from one place instead of
being edited across templates.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.domain.enums import InvoiceStatus, TaskStatus, TaskType, UserRole
from app.web.navigation import nav_for

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Called at render time, so the top bar always shows the current date, not the
# date the process started: templates use {{ now() }}.
templates.env.globals["now"] = datetime.now

# Enums are exposed so templates never hard-code status/type strings.
templates.env.globals["TaskStatus"] = TaskStatus
templates.env.globals["TaskType"] = TaskType
templates.env.globals["UserRole"] = UserRole
templates.env.globals["InvoiceStatus"] = InvoiceStatus

# Top-bar links, filtered by role: {% for link in nav_for(current_user.role) %}.
templates.env.globals["nav_for"] = nav_for

# Product wording, used by the top bar and the sign-in card. Change the name
# through the APP_NAME environment variable and the tagline here.
templates.env.globals["brand_name"] = get_settings().app_name
templates.env.globals["brand_tagline"] = "Local Operations & Optimization Platform"

# The stylesheets base.html links, in order. Tokens first, rules second; append
# a file here to add a stylesheet without touching any template.
templates.env.globals["stylesheets"] = ("/static/theme.css", "/static/app.css")

# Wording of the strip base.html shows to signed-in demo visitors, or None on a
# real instance, where the strip is not rendered at all.
templates.env.globals["demo_notice"] = (
    get_settings().demo_reset_note if get_settings().demo_mode else None
)


def _money(value) -> str:
    if value in (None, ""):
        return ""
    return f"{Decimal(value):,.2f}"


templates.env.filters["money"] = _money
