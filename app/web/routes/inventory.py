"""Inventory pages.

Listing is open to both roles — engineers need it to record what they fitted —
but every write is proprietor-only, enforced in InventoryService.
"""

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.core.deps import CurrentUser, DbSession, Proprietor
from app.services.inventory_service import InventoryService
from app.web.templating import templates

router = APIRouter(prefix="/inventory", tags=["web"])


@router.get("")
def inventory_list(request: Request, db: DbSession, user: CurrentUser, q: str | None = None):
    service = InventoryService(db)
    return templates.TemplateResponse(
        request,
        "inventory/list.html",
        {
            "current_user": user,
            "items": service.list_items(user, search=q),
            "low_stock": service.list_low_stock(),
            "search": q or "",
        },
    )


@router.get("/new")
def new_item_page(request: Request, user: Proprietor):
    return templates.TemplateResponse(
        request, "inventory/new.html", {"current_user": user}
    )


@router.post("/new")
def create_item(
    db: DbSession,
    user: Proprietor,
    sku: str = Form(...),
    name: str = Form(...),
    category: str = Form(default=""),
    hsn_code: str = Form(default=""),
    purchase_price: str = Form(default=""),
    selling_price: str = Form(default=""),
    stock_qty: str = Form(default="0"),
    min_stock: str = Form(default="0"),
):
    InventoryService(db).create_item(
        user,
        sku=sku,
        name=name,
        category=category,
        hsn_code=hsn_code,
        purchase_price=purchase_price,
        selling_price=selling_price,
        stock_qty=stock_qty,
        min_stock=min_stock,
    )
    return RedirectResponse("/inventory", status_code=303)


@router.post("/{item_id}/stock")
def adjust_stock(db: DbSession, user: Proprietor, item_id: int, stock_qty: str = Form(...)):
    InventoryService(db).adjust_stock(user, item_id, stock_qty)
    return RedirectResponse("/inventory", status_code=303)
