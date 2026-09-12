"""Jinja environment for the application UI (separate from quotation formats)."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.domain.enums import TaskStatus, TaskType

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Called at render time, so the top bar always shows the current date, not the
# date the process started: templates use {{ now() }}.
templates.env.globals["now"] = datetime.now

# Enums are exposed so templates never hard-code status/type strings.
templates.env.globals["TaskStatus"] = TaskStatus
templates.env.globals["TaskType"] = TaskType


def _money(value) -> str:
    if value in (None, ""):
        return ""
    return f"{Decimal(value):,.2f}"


templates.env.filters["money"] = _money
