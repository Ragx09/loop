from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Customer(TimestampMixin, Base):
    """A customer the business works for.

    Tasks and quotations kept their free-text ``customer_name`` when this table
    arrived, and the link to a Customer row is optional on both. Existing
    records therefore keep working exactly as before, and a customer can be
    attached to them later without a data migration.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)

    phone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    equipment: Mapped[list["Equipment"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="Equipment.name",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Customer #{self.id} {self.name}>"


class Equipment(TimestampMixin, Base):
    """A machine installed at a customer's site."""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    installed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="equipment")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Equipment #{self.id} {self.name}>"
