"""Invoicing and payments.

Every price and tax rate is entered by hand, exactly as for quotations. The only
value LOOP derives is the invoice *status*, which follows from the payments
recorded against it and is never set directly.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.domain.enums import InvoiceStatus, PaymentMethod, UserRole
from app.models.business import Business
from app.models.invoice import Invoice, InvoiceItem, Payment
from app.models.user import User
from app.repositories.business_repository import BusinessRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.quotation_repository import QuotationRepository


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.invoices = InvoiceRepository(db)
        self.businesses = BusinessRepository(db)
        self.customers = CustomerRepository(db)
        self.quotations = QuotationRepository(db)

    # --- reads -----------------------------------------------------------
    def list_invoices(self, actor: User, customer_id: int | None = None) -> list[Invoice]:
        self._assert_proprietor(actor)
        invoices = self.invoices.list(customer_id=customer_id)
        for invoice in invoices:
            self._refresh_status(invoice)
        return invoices

    def get(self, actor: User, invoice_id: int) -> Invoice:
        self._assert_proprietor(actor)
        invoice = self.invoices.get(invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice not found.")
        self._refresh_status(invoice)
        return invoice

    def list_businesses(self) -> list[Business]:
        return self.businesses.list_active()

    def payment_summary(self, actor: User) -> dict:
        """The numbers the payments dashboard shows."""
        self._assert_proprietor(actor)
        invoices = self.list_invoices(actor)
        today = date.today()

        outstanding = sum((i.balance_due for i in invoices), Decimal("0"))
        overdue = sum(
            (i.balance_due for i in invoices if i.status is InvoiceStatus.OVERDUE),
            Decimal("0"),
        )
        collected_total = sum((i.amount_paid for i in invoices), Decimal("0"))
        collected_today = sum(
            (
                Decimal(p.amount)
                for i in invoices
                for p in i.payments
                if p.paid_at == today
            ),
            Decimal("0"),
        )

        return {
            "invoices": invoices,
            "invoiced_total": sum((i.total for i in invoices), Decimal("0")),
            "outstanding": outstanding,
            "overdue": overdue,
            "collected_total": collected_total,
            "collected_today": collected_today,
            "unpaid": [i for i in invoices if i.balance_due > 0],
        }

    # --- writes ----------------------------------------------------------
    def create_invoice(
        self,
        actor: User,
        *,
        business_id: int,
        customer_id: int,
        items: list[dict],
        invoice_date: date | None = None,
        due_date: date | None = None,
        invoice_number: str | None = None,
        quotation_id: int | None = None,
        is_interstate: bool = False,
        notes: str | None = None,
    ) -> Invoice:
        self._assert_proprietor(actor)

        business = self.businesses.get(business_id)
        if business is None or not business.is_active:
            raise ValidationError("Select a valid business.")

        customer = self.customers.get(customer_id)
        if customer is None:
            raise ValidationError("Select a valid customer.")

        invoice_date = invoice_date or date.today()
        parsed_items = self._parse_items(items)

        invoice = Invoice(
            invoice_number=(invoice_number or "").strip()
            or self._next_invoice_number(business, invoice_date),
            invoice_date=invoice_date,
            due_date=due_date,
            business_id=business.id,
            customer_id=customer.id,
            quotation_id=quotation_id,
            status=InvoiceStatus.PENDING,
            is_interstate=bool(is_interstate),
            notes=(notes or "").strip() or None,
            created_by_id=actor.id,
            items=parsed_items,
        )
        self.invoices.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_from_quotation(
        self, actor: User, quotation_id: int, *, customer_id: int, tax_rate="18", **kwargs
    ) -> Invoice:
        """Copy a quotation's lines onto a new invoice.

        The lines are copied, not shared: editing the invoice afterwards must
        never rewrite the quotation that was already sent to the customer.
        """
        self._assert_proprietor(actor)

        quotation = self.quotations.get(quotation_id)
        if quotation is None:
            raise NotFoundError("Quotation not found.")

        items = [
            {
                "particulars": item.particulars,
                "hsn_code": item.hsn_code,
                "price": item.price,
                "quantity": item.quantity,
                "tax_rate": tax_rate,
            }
            for item in quotation.items
        ]

        return self.create_invoice(
            actor,
            business_id=quotation.business_id,
            customer_id=customer_id,
            items=items,
            quotation_id=quotation.id,
            notes=quotation.notes,
            **kwargs,
        )

    def record_payment(
        self,
        actor: User,
        invoice_id: int,
        *,
        amount,
        method: PaymentMethod,
        paid_at: date | None = None,
        reference: str | None = None,
        notes: str | None = None,
    ) -> Payment:
        self._assert_proprietor(actor)
        invoice = self.get(actor, invoice_id)

        value = _parse_amount(amount)
        if value > invoice.balance_due:
            raise ValidationError(
                f"That is more than the {invoice.balance_due:,.2f} still due."
            )

        payment = Payment(
            invoice_id=invoice.id,
            amount=value,
            method=method,
            paid_at=paid_at or date.today(),
            reference=(reference or "").strip() or None,
            notes=(notes or "").strip() or None,
        )
        self.invoices.add_payment(payment)
        self.db.flush()
        self.db.refresh(invoice)
        self._refresh_status(invoice)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    # --- helpers ---------------------------------------------------------
    def _refresh_status(self, invoice: Invoice) -> None:
        """Derive the status from payments. Never set by hand."""
        paid = invoice.amount_paid
        total = invoice.total

        if total > 0 and paid >= total:
            status = InvoiceStatus.PAID
        elif paid > 0:
            status = InvoiceStatus.PARTIALLY_PAID
        elif invoice.due_date is not None and invoice.due_date < date.today():
            status = InvoiceStatus.OVERDUE
        else:
            status = InvoiceStatus.PENDING

        if invoice.status is not status:
            invoice.status = status

    def _parse_items(self, items: list[dict]) -> list[InvoiceItem]:
        parsed: list[InvoiceItem] = []
        for position, raw in enumerate(items or []):
            particulars = (raw.get("particulars") or "").strip()
            raw_price = raw.get("price")
            hsn_code = (raw.get("hsn_code") or "").strip() or None

            # The entry form always submits blank rows; skip them.
            if not particulars and raw_price in (None, "") and not hsn_code:
                continue
            if not particulars:
                raise ValidationError("Every invoice line needs particulars.")

            parsed.append(
                InvoiceItem(
                    position=position,
                    particulars=particulars,
                    hsn_code=hsn_code,
                    price=_parse_amount(raw_price),
                    quantity=_parse_quantity(raw.get("quantity")),
                    tax_rate=_parse_rate(raw.get("tax_rate")),
                )
            )

        if not parsed:
            raise ValidationError("Add at least one invoice line.")
        return parsed

    def _next_invoice_number(self, business: Business, on_date: date) -> str:
        prefix = "".join(p[0] for p in business.name.split() if p)[:3].upper() or "IN"
        sequence = self.invoices.count_for_year(business.id, on_date.year) + 1
        return f"{prefix}/INV/{on_date.year}/{sequence:04d}"

    @staticmethod
    def _assert_proprietor(actor: User) -> None:
        if actor.role is not UserRole.PROPRIETOR:
            raise PermissionDeniedError("Only the proprietor can manage invoices.")


def _parse_amount(value) -> Decimal:
    if value in (None, ""):
        raise ValidationError("An amount is required.")
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError("Amounts must be numbers.")
    if amount <= 0:
        raise ValidationError("Amounts must be greater than zero.")
    return amount


def _parse_quantity(value) -> int:
    if value in (None, ""):
        return 1
    try:
        qty = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a whole number.")
    if qty < 1:
        raise ValidationError("Quantity must be at least 1.")
    return qty


def _parse_rate(value) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    try:
        rate = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError("Tax rate must be a number.")
    if rate < 0 or rate > 100:
        raise ValidationError("Tax rate must be between 0 and 100.")
    return rate
