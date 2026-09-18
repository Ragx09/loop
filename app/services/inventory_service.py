"""Stock and materials business logic.

The only stock movement LOOP performs is the decrement when an engineer records
a material used on a job. There is no purchasing, no reorder automation and no
valuation — stock levels are otherwise maintained by hand.
"""

from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.domain.enums import UserRole
from app.models.inventory import InventoryItem, MaterialUsed
from app.models.user import User
from app.repositories.inventory_repository import InventoryRepository


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.items = InventoryRepository(db)

    # --- reads -----------------------------------------------------------
    def list_items(self, actor: User, search: str | None = None) -> list[InventoryItem]:
        # Engineers need the list to record what they used on a job.
        return self.items.list(search=search)

    def list_low_stock(self) -> list[InventoryItem]:
        return self.items.list_low_stock()

    def get(self, actor: User, item_id: int) -> InventoryItem:
        item = self.items.get(item_id)
        if item is None:
            raise NotFoundError("Inventory item not found.")
        return item

    # --- writes ----------------------------------------------------------
    def create_item(
        self,
        actor: User,
        *,
        sku: str,
        name: str,
        category: str | None = None,
        hsn_code: str | None = None,
        purchase_price=None,
        selling_price=None,
        stock_qty=0,
        min_stock=0,
    ) -> InventoryItem:
        self._assert_proprietor(actor)

        sku = (sku or "").strip().upper()
        name = (name or "").strip()
        if not sku:
            raise ValidationError("SKU is required.")
        if not name:
            raise ValidationError("Item name is required.")
        if self.items.get_by_sku(sku) is not None:
            raise ValidationError(f"SKU {sku} already exists.")

        item = InventoryItem(
            sku=sku,
            name=name,
            category=_clean(category),
            hsn_code=_clean(hsn_code),
            purchase_price=_optional_price(purchase_price),
            selling_price=_optional_price(selling_price),
            stock_qty=_parse_qty(stock_qty, allow_zero=True),
            min_stock=_parse_qty(min_stock, allow_zero=True),
            is_active=True,
        )
        self.items.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def adjust_stock(self, actor: User, item_id: int, new_qty) -> InventoryItem:
        """Set the stock level by hand, e.g. after a delivery or a stock count."""
        self._assert_proprietor(actor)
        item = self.get(actor, item_id)
        item.stock_qty = _parse_qty(new_qty, allow_zero=True)
        self.db.commit()
        self.db.refresh(item)
        return item

    def record_material_used(
        self, actor: User, task, item_id: int, quantity, commit: bool = True
    ) -> MaterialUsed:
        """Consume stock against a task.

        Authorization of the *task* is the caller's job (TaskService); this
        method owns the stock rules only.
        """
        item = self.get(actor, item_id)
        qty = _parse_qty(quantity)

        if qty > item.stock_qty:
            raise ValidationError(
                f"Only {item.stock_qty} of {item.name} left in stock."
            )

        item.stock_qty -= qty
        material = MaterialUsed(task_id=task.id, inventory_item_id=item.id, quantity=qty)
        self.items.add_material(material)

        if commit:
            self.db.commit()
            self.db.refresh(material)
        return material

    @staticmethod
    def _assert_proprietor(actor: User) -> None:
        if actor.role is not UserRole.PROPRIETOR:
            raise PermissionDeniedError("Only the proprietor can manage inventory.")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _optional_price(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        price = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError("Prices must be numbers.")
    if price < 0:
        raise ValidationError("Prices cannot be negative.")
    return price


def _parse_qty(value, allow_zero: bool = False) -> int:
    try:
        qty = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError("Quantity must be a whole number.")
    if qty < 0 or (qty == 0 and not allow_zero):
        raise ValidationError("Quantity must be a positive whole number.")
    return qty
