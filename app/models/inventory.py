from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class InventoryItem(TimestampMixin, Base):
    """A part or product held in stock.

    ``selling_price`` is a convenience default the proprietor may accept or
    overwrite when building a quotation or invoice — it is never applied
    automatically, because the same product goes out at different prices for
    different customers.
    """

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)

    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    hsn_code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    selling_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @property
    def is_low_stock(self) -> bool:
        return self.stock_qty <= self.min_stock

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<InventoryItem {self.sku}>"


class MaterialUsed(Base):
    """A part consumed on a task, recorded by the engineer doing the work.

    Recording one decrements the item's stock; the quantity is kept here so the
    service report can list what went into the job.
    """

    __tablename__ = "materials_used"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inventory_item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    item: Mapped["InventoryItem"] = relationship(lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<MaterialUsed task={self.task_id} item={self.inventory_item_id}>"
