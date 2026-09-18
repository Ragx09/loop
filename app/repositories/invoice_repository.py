"""Data access for invoices and payments."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, Payment


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, invoice_id: int) -> Invoice | None:
        return self.db.get(Invoice, invoice_id)

    def list(self, customer_id: int | None = None) -> list[Invoice]:
        stmt = select(Invoice)
        if customer_id is not None:
            stmt = stmt.where(Invoice.customer_id == customer_id)
        return list(self.db.execute(stmt.order_by(Invoice.id.desc())).scalars())

    def list_for_quotation(self, quotation_id: int) -> list[Invoice]:
        stmt = select(Invoice).where(Invoice.quotation_id == quotation_id)
        return list(self.db.execute(stmt).scalars())

    def count_for_year(self, business_id: int, year: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Invoice)
            .where(
                Invoice.business_id == business_id,
                Invoice.invoice_date >= date(year, 1, 1),
                Invoice.invoice_date <= date(year, 12, 31),
            )
        )
        return self.db.execute(stmt).scalar_one()

    def add(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        return invoice

    # --- payments --------------------------------------------------------
    def add_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def list_payments(self) -> list[Payment]:
        return list(self.db.execute(select(Payment).order_by(Payment.paid_at.desc())).scalars())
