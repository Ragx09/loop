"""Invoice and payment pages — proprietor only."""

from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.core.deps import DbSession, Proprietor
from app.documents.renderer import DocumentRenderer
from app.domain.enums import PaymentMethod
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.quotation_service import QuotationService
from app.web.templating import templates

router = APIRouter(prefix="/invoices", tags=["web"])


@router.get("")
def invoice_list(request: Request, db: DbSession, user: Proprietor):
    return templates.TemplateResponse(
        request,
        "invoices/list.html",
        {"current_user": user, "invoices": InvoiceService(db).list_invoices(user)},
    )


@router.get("/payments")
def payments_dashboard(request: Request, db: DbSession, user: Proprietor):
    return templates.TemplateResponse(
        request,
        "invoices/payments.html",
        {"current_user": user, **InvoiceService(db).payment_summary(user)},
    )


@router.get("/new")
def new_invoice_page(
    request: Request, db: DbSession, user: Proprietor, from_quotation: int | None = None
):
    service = InvoiceService(db)
    quotation = None
    if from_quotation is not None:
        quotation = QuotationService(db).get(user, from_quotation)

    return templates.TemplateResponse(
        request,
        "invoices/new.html",
        {
            "current_user": user,
            "businesses": service.list_businesses(),
            "customers": CustomerService(db).list_customers(user),
            "today": date.today().isoformat(),
            "blank_rows": range(5),
            "quotation": quotation,
        },
    )


@router.post("/new")
async def create_invoice(request: Request, db: DbSession, user: Proprietor):
    """Line items arrive as parallel form arrays, as they do for quotations."""
    form = await request.form()
    items = [
        {"particulars": p, "hsn_code": h, "price": pr, "quantity": q, "tax_rate": t}
        for p, h, pr, q, t in zip(
            form.getlist("particulars"),
            form.getlist("hsn_code"),
            form.getlist("price"),
            form.getlist("quantity"),
            form.getlist("tax_rate"),
        )
    ]

    due = form.get("due_date")
    quotation_id = form.get("quotation_id")

    invoice = InvoiceService(db).create_invoice(
        user,
        business_id=int(form.get("business_id")),
        customer_id=int(form.get("customer_id")),
        items=items,
        invoice_date=date.fromisoformat(str(form.get("invoice_date"))),
        due_date=date.fromisoformat(str(due)) if due else None,
        invoice_number=str(form.get("invoice_number", "")),
        quotation_id=int(quotation_id) if quotation_id else None,
        is_interstate=form.get("is_interstate") == "on",
        notes=str(form.get("notes", "")),
    )
    return RedirectResponse(f"/invoices/{invoice.id}", status_code=303)


@router.get("/{invoice_id}")
def invoice_detail(request: Request, db: DbSession, user: Proprietor, invoice_id: int):
    return templates.TemplateResponse(
        request,
        "invoices/detail.html",
        {
            "current_user": user,
            "invoice": InvoiceService(db).get(user, invoice_id),
            "methods": list(PaymentMethod),
            "today": date.today().isoformat(),
        },
    )


@router.post("/{invoice_id}/payments")
def record_payment(
    db: DbSession,
    user: Proprietor,
    invoice_id: int,
    amount: str = Form(...),
    method: str = Form(...),
    paid_at: str = Form(default=""),
    reference: str = Form(default=""),
):
    InvoiceService(db).record_payment(
        user,
        invoice_id,
        amount=amount,
        method=PaymentMethod(method),
        paid_at=date.fromisoformat(paid_at) if paid_at else None,
        reference=reference,
    )
    return RedirectResponse(f"/invoices/{invoice_id}", status_code=303)


@router.get("/{invoice_id}/pdf")
def invoice_pdf(db: DbSession, user: Proprietor, invoice_id: int):
    invoice = InvoiceService(db).get(user, invoice_id)
    filename, pdf = DocumentRenderer().invoice_pdf(invoice)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
