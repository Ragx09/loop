"""Read-only rollups for the owner dashboard.

Every number here is derived from the other modules at read time. Nothing is
cached or stored, so the dashboard cannot disagree with the underlying records.
"""

from collections import OrderedDict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import PermissionDeniedError
from app.domain.enums import InvoiceStatus, TaskStatus, UserRole
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.task import Task
from app.models.user import User
from app.repositories.inventory_repository import InventoryRepository
from app.services.invoice_service import InvoiceService

MONTHS_SHOWN = 6


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self, actor: User) -> dict:
        if actor.role is not UserRole.PROPRIETOR:
            raise PermissionDeniedError("Only the proprietor can view the dashboard.")

        tasks = list(self.db.execute(select(Task)).unique().scalars())
        invoices = InvoiceService(self.db).list_invoices(actor)
        customers = list(self.db.execute(select(Customer)).scalars())
        low_stock = InventoryRepository(self.db).list_low_stock()
        today = date.today()

        by_status = {
            status: sum(1 for t in tasks if t.status is status) for status in TaskStatus
        }

        return {
            # Headline counters
            "customer_count": len(customers),
            "task_count": len(tasks),
            "tasks_today": [t for t in tasks if t.scheduled_date == today],
            "open_tasks": sum(
                1 for t in tasks if t.status is not TaskStatus.COMPLETED
            ),
            "completed_tasks": by_status.get(TaskStatus.COMPLETED, 0),
            "tasks_by_status": by_status,
            # Money
            "invoiced_total": _sum(i.total for i in invoices),
            "collected_total": _sum(i.amount_paid for i in invoices),
            "outstanding_total": _sum(i.balance_due for i in invoices),
            "overdue_total": _sum(
                i.balance_due for i in invoices if i.status is InvoiceStatus.OVERDUE
            ),
            # Charts
            "revenue_by_month": self._revenue_by_month(invoices),
            "tasks_by_month": self._tasks_by_month(tasks),
            "top_customers": self._top_customers(invoices),
            "engineer_completions": self._engineer_completions(tasks),
            "low_stock": low_stock,
        }

    # --- chart series ----------------------------------------------------
    def _months(self) -> list[str]:
        today = date.today()
        months = []
        year, month = today.year, today.month
        for _ in range(MONTHS_SHOWN):
            months.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month, year = 12, year - 1
        return list(reversed(months))

    def _revenue_by_month(self, invoices: list[Invoice]) -> list[dict]:
        buckets = OrderedDict((m, Decimal("0")) for m in self._months())
        for invoice in invoices:
            key = invoice.invoice_date.strftime("%Y-%m")
            if key in buckets:
                buckets[key] += invoice.total
        return [{"label": _month_label(k), "value": v} for k, v in buckets.items()]

    def _tasks_by_month(self, tasks: list[Task]) -> list[dict]:
        buckets = OrderedDict((m, 0) for m in self._months())
        for task in tasks:
            key = task.scheduled_date.strftime("%Y-%m")
            if key in buckets:
                buckets[key] += 1
        return [{"label": _month_label(k), "value": v} for k, v in buckets.items()]

    def _top_customers(self, invoices: list[Invoice]) -> list[dict]:
        totals: dict[str, Decimal] = {}
        for invoice in invoices:
            name = invoice.customer.name
            totals[name] = totals.get(name, Decimal("0")) + invoice.total
        ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:5]
        return [{"label": name, "value": total} for name, total in ranked]

    def _engineer_completions(self, tasks: list[Task]) -> list[dict]:
        totals: dict[str, int] = {}
        for task in tasks:
            if task.status is TaskStatus.COMPLETED and task.assigned_engineer is not None:
                name = task.assigned_engineer.full_name
                totals[name] = totals.get(name, 0) + 1
        ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        return [{"label": name, "value": count} for name, count in ranked]


def _sum(values) -> Decimal:
    return sum(values, Decimal("0"))


def _month_label(key: str) -> str:
    year, month = key.split("-")
    names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    return f"{names[int(month) - 1]} {year[2:]}"
