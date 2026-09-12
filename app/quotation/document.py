"""Transport-agnostic data passed to a quotation template.

Deliberately plain dataclasses rather than ORM objects: a template must not be
able to trigger database access, and documents can be rendered in tests without
a database.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class BusinessInfo:
    key: str
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None


@dataclass(frozen=True)
class QuotationLine:
    particulars: str
    price: Decimal
    hsn_code: str | None = None
    quantity: int = 1

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.price) * (self.quantity or 1)


@dataclass(frozen=True)
class QuotationDocument:
    business: BusinessInfo
    quotation_number: str
    quotation_date: date
    customer_name: str
    lines: list[QuotationLine] = field(default_factory=list)
    customer_address: str | None = None
    notes: str | None = None

    @property
    def total(self) -> Decimal:
        """Sum of the line totals. There is no pricing logic."""
        return sum((line.line_total for line in self.lines), Decimal("0"))
