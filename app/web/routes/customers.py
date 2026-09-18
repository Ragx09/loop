"""Customer and equipment pages — proprietor only (enforced again in the service)."""

from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.core.deps import DbSession, Proprietor
from app.services.customer_service import CustomerService
from app.web.templating import templates

router = APIRouter(prefix="/customers", tags=["web"])


@router.get("")
def customer_list(request: Request, db: DbSession, user: Proprietor, q: str | None = None):
    return templates.TemplateResponse(
        request,
        "customers/list.html",
        {
            "current_user": user,
            "customers": CustomerService(db).list_customers(user, search=q),
            "search": q or "",
        },
    )


@router.get("/new")
def new_customer_page(request: Request, user: Proprietor):
    return templates.TemplateResponse(
        request, "customers/new.html", {"current_user": user}
    )


@router.post("/new")
def create_customer(
    db: DbSession,
    user: Proprietor,
    name: str = Form(...),
    phone: str = Form(default=""),
    email: str = Form(default=""),
    address: str = Form(default=""),
    gstin: str = Form(default=""),
    notes: str = Form(default=""),
):
    customer = CustomerService(db).create_customer(
        user,
        name=name,
        phone=phone,
        email=email,
        address=address,
        gstin=gstin,
        notes=notes,
    )
    return RedirectResponse(f"/customers/{customer.id}", status_code=303)


@router.get("/{customer_id}")
def customer_detail(request: Request, db: DbSession, user: Proprietor, customer_id: int):
    return templates.TemplateResponse(
        request,
        "customers/detail.html",
        {"current_user": user, **CustomerService(db).history(user, customer_id)},
    )


@router.post("/{customer_id}/equipment")
def add_equipment(
    db: DbSession,
    user: Proprietor,
    customer_id: int,
    name: str = Form(...),
    model: str = Form(default=""),
    serial_number: str = Form(default=""),
    installed_at: str = Form(default=""),
    notes: str = Form(default=""),
):
    CustomerService(db).add_equipment(
        user,
        customer_id,
        name=name,
        model=model,
        serial_number=serial_number,
        installed_at=date.fromisoformat(installed_at) if installed_at else None,
        notes=notes,
    )
    return RedirectResponse(f"/customers/{customer_id}", status_code=303)
