"""Customer and equipment business logic.

Engineers may read customers (they need the site details of the job they are
on) but only the proprietor may change them.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.domain.enums import UserRole
from app.models.customer import Customer, Equipment
from app.models.invoice import Invoice
from app.models.quotation import Quotation
from app.models.task import Task
from app.models.user import User
from app.repositories.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.customers = CustomerRepository(db)

    # --- reads -----------------------------------------------------------
    def list_customers(self, actor: User, search: str | None = None) -> list[Customer]:
        return self.customers.list(search=search)

    def get(self, actor: User, customer_id: int) -> Customer:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise NotFoundError("Customer not found.")
        return customer

    def history(self, actor: User, customer_id: int) -> dict:
        """Everything LOOP knows about one customer, for the detail page."""
        self._assert_proprietor(actor)
        customer = self.get(actor, customer_id)

        tasks = list(
            self.db.execute(
                select(Task)
                .where(Task.customer_id == customer.id)
                .order_by(Task.scheduled_date.desc())
            ).scalars()
        )
        quotations = list(
            self.db.execute(
                select(Quotation)
                .where(Quotation.customer_name == customer.name)
                .order_by(Quotation.id.desc())
            ).scalars()
        )
        invoices = list(
            self.db.execute(
                select(Invoice)
                .where(Invoice.customer_id == customer.id)
                .order_by(Invoice.id.desc())
            ).scalars()
        )

        return {
            "customer": customer,
            "tasks": tasks,
            "quotations": quotations,
            "invoices": invoices,
            # "Lifetime value" here means invoiced, not collected.
            "invoiced_total": sum((inv.total for inv in invoices), start=_zero()),
            "outstanding_total": sum((inv.balance_due for inv in invoices), start=_zero()),
        }

    # --- writes ----------------------------------------------------------
    def create_customer(
        self,
        actor: User,
        *,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        gstin: str | None = None,
        notes: str | None = None,
    ) -> Customer:
        self._assert_proprietor(actor)

        name = (name or "").strip()
        if not name:
            raise ValidationError("Customer name is required.")

        customer = Customer(
            name=name,
            phone=_clean(phone),
            email=_clean(email),
            address=_clean(address),
            gstin=_clean(gstin),
            notes=_clean(notes),
            is_active=True,
        )
        self.customers.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def update_customer(self, actor: User, customer_id: int, **fields) -> Customer:
        self._assert_proprietor(actor)
        customer = self.get(actor, customer_id)

        if "name" in fields:
            name = (fields["name"] or "").strip()
            if not name:
                raise ValidationError("Customer name is required.")
            customer.name = name

        for field in ("phone", "email", "address", "gstin", "notes"):
            if field in fields:
                setattr(customer, field, _clean(fields[field]))

        self.db.commit()
        self.db.refresh(customer)
        return customer

    def add_equipment(
        self,
        actor: User,
        customer_id: int,
        *,
        name: str,
        model: str | None = None,
        serial_number: str | None = None,
        installed_at: date | None = None,
        notes: str | None = None,
    ) -> Equipment:
        self._assert_proprietor(actor)
        customer = self.get(actor, customer_id)

        name = (name or "").strip()
        if not name:
            raise ValidationError("Equipment name is required.")

        equipment = Equipment(
            customer_id=customer.id,
            name=name,
            model=_clean(model),
            serial_number=_clean(serial_number),
            installed_at=installed_at,
            notes=_clean(notes),
        )
        self.customers.add_equipment(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    @staticmethod
    def _assert_proprietor(actor: User) -> None:
        if actor.role is not UserRole.PROPRIETOR:
            raise PermissionDeniedError("Only the proprietor can manage customers.")


def _zero():
    from decimal import Decimal

    return Decimal("0")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
