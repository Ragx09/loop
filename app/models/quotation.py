from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Quotation(TimestampMixin, Base):
    """A quotation issued by a business, rendered through a chosen template.

    The template is referenced by key only: layouts live in the quotation module,
    never in the database or in business logic.
    """

    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_number: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    quotation_date: Mapped[date] = mapped_column(Date, nullable=False)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    #: Key of the template used to render this quotation, e.g. "standard".
    template_key: Mapped[str] = mapped_column(String(64), nullable=False)

    customer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    customer_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    business: Mapped["Business"] = relationship(lazy="joined")  # noqa: F821
    created_by: Mapped["User"] = relationship(lazy="joined")  # noqa: F821
    items: Mapped[list["QuotationItem"]] = relationship(
        back_populates="quotation",
        cascade="all, delete-orphan",
        order_by="QuotationItem.position",
        lazy="selectin",
    )

    @property
    def total(self) -> Decimal:
        """Plain sum of the manually entered line totals. No pricing rules."""
        return sum((item.line_total for item in self.items), Decimal("0"))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Quotation {self.quotation_number}>"


class QuotationItem(Base):
    """One line of a quotation. Prices are always entered manually."""

    __tablename__ = "quotation_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    particulars: Mapped[str] = mapped_column(String(500), nullable=False)
    hsn_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: Unit price for a single quantity. Always entered by hand.
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    quotation: Mapped["Quotation"] = relationship(back_populates="items")

    @property
    def line_total(self) -> Decimal:
        """Unit price x quantity. Arithmetic only — still no pricing rules."""
        return Decimal(self.price) * (self.quantity or 1)
