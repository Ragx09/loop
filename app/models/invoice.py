from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.enums import InvoiceStatus, PaymentMethod


class Invoice(TimestampMixin, Base):
    """A tax invoice issued by a business.

    Like quotations, every price is entered by hand. The only arithmetic here is
    summing lines and splitting the tax — there is no pricing logic.
    """

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    #: Set when the invoice was converted from a quotation, so the trail is kept.
    quotation_id: Mapped[int | None] = mapped_column(
        ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    #: Stored, but only ever written by InvoiceService from the payments recorded.
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(
            InvoiceStatus,
            name="invoice_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
    )

    #: True when the customer is in another state: one IGST line instead of
    #: CGST + SGST. The proprietor chooses; nothing is inferred from an address.
    is_interstate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    business: Mapped["Business"] = relationship(lazy="joined")  # noqa: F821
    customer: Mapped["Customer"] = relationship(lazy="joined")  # noqa: F821
    created_by: Mapped["User"] = relationship(lazy="joined")  # noqa: F821
    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.position",
        lazy="selectin",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="Payment.paid_at",
        lazy="selectin",
    )

    # --- derived totals (never stored, so they cannot go stale) ----------
    @property
    def subtotal(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0"))

    @property
    def tax_total(self) -> Decimal:
        return sum((item.tax_amount for item in self.items), Decimal("0"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax_total

    @property
    def amount_paid(self) -> Decimal:
        return sum((Decimal(p.amount) for p in self.payments), Decimal("0"))

    @property
    def balance_due(self) -> Decimal:
        return self.total - self.amount_paid

    @property
    def tax_breakdown(self) -> list[dict]:
        """Tax grouped by rate, split the way the invoice will print it."""
        by_rate: dict[Decimal, Decimal] = {}
        for item in self.items:
            rate = Decimal(item.tax_rate)
            by_rate[rate] = by_rate.get(rate, Decimal("0")) + item.tax_amount

        rows = []
        for rate in sorted(by_rate):
            amount = by_rate[rate]
            if self.is_interstate:
                rows.append({"label": f"IGST @ {rate}%", "amount": amount})
            else:
                half = (amount / 2).quantize(Decimal("0.01"))
                rows.append({"label": f"CGST @ {rate / 2}%", "amount": half})
                rows.append({"label": f"SGST @ {rate / 2}%", "amount": amount - half})
        return rows

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Invoice {self.invoice_number}>"


class InvoiceItem(Base):
    """One line of an invoice. Price and tax rate are both entered by hand."""

    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    particulars: Mapped[str] = mapped_column(String(500), nullable=False)
    hsn_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    #: Percentage, e.g. 18 for 18% GST.
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    invoice: Mapped["Invoice"] = relationship(back_populates="items")

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.price) * (self.quantity or 1)

    @property
    def tax_amount(self) -> Decimal:
        return (self.line_total * Decimal(self.tax_rate) / 100).quantize(Decimal("0.01"))


class Payment(TimestampMixin, Base):
    """Money received against an invoice. Recorded by hand: LOOP takes no
    payments itself and integrates with no gateway."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(
            PaymentMethod,
            name="payment_method",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Payment #{self.id} {self.amount}>"
