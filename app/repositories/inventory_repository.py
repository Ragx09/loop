"""Data access for stock items and the materials consumed on jobs."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryItem, MaterialUsed


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, item_id: int) -> InventoryItem | None:
        return self.db.get(InventoryItem, item_id)

    def get_by_sku(self, sku: str) -> InventoryItem | None:
        stmt = select(InventoryItem).where(InventoryItem.sku == sku)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, search: str | None = None, active_only: bool = True) -> list[InventoryItem]:
        stmt = select(InventoryItem)
        if active_only:
            stmt = stmt.where(InventoryItem.is_active.is_(True))
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(InventoryItem.name.ilike(like) | InventoryItem.sku.ilike(like))
        return list(self.db.execute(stmt.order_by(InventoryItem.name)).scalars())

    def list_low_stock(self) -> list[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .where(InventoryItem.is_active.is_(True))
            .where(InventoryItem.stock_qty <= InventoryItem.min_stock)
            .order_by(InventoryItem.name)
        )
        return list(self.db.execute(stmt).scalars())

    def add(self, item: InventoryItem) -> InventoryItem:
        self.db.add(item)
        self.db.flush()
        return item

    # --- materials used --------------------------------------------------
    def get_material(self, material_id: int) -> MaterialUsed | None:
        return self.db.get(MaterialUsed, material_id)

    def add_material(self, material: MaterialUsed) -> MaterialUsed:
        self.db.add(material)
        self.db.flush()
        return material
