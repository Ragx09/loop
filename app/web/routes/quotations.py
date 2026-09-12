"""Quotation pages — proprietor only (enforced by the Proprietor dependency
and again inside QuotationService)."""

from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.core.deps import DbSession, Proprietor
from app.services.quotation_service import QuotationService
from app.web.templating import templates

router = APIRouter(prefix="/quotations", tags=["web"])


@router.get("")
def quotation_list(request: Request, db: DbSession, user: Proprietor):
    service = QuotationService(db)
    return templates.TemplateResponse(
        request,
        "quotations/list.html",
        {"current_user": user, "quotations": service.list_quotations(user)},
    )


@router.get("/new")
def new_quotation_page(request: Request, db: DbSession, user: Proprietor):
    service = QuotationService(db)
    return templates.TemplateResponse(
        request,
        "quotations/new.html",
        {
            "current_user": user,
            "businesses": service.list_businesses(),
            "templates_available": service.list_templates(),
            "today": date.today().isoformat(),
            "blank_rows": range(5),
        },
    )


@router.post("/new")
async def create_quotation(request: Request, db: DbSession, user: Proprietor):
    """Line items arrive as parallel form arrays, so the raw form is read here."""
    form = await request.form()
    particulars = form.getlist("particulars")
    hsn_codes = form.getlist("hsn_code")
    prices = form.getlist("price")
    quantities = form.getlist("quantity")

    items = [
        {"particulars": p, "hsn_code": h, "price": pr, "quantity": q}
        for p, h, pr, q in zip(particulars, hsn_codes, prices, quantities)
    ]

    quotation = QuotationService(db).create_quotation(
        user,
        business_id=int(form.get("business_id")),
        template_key=str(form.get("template_key")),
        customer_name=str(form.get("customer_name", "")),
        customer_address=str(form.get("customer_address", "")),
        quotation_number=str(form.get("quotation_number", "")),
        quotation_date=date.fromisoformat(str(form.get("quotation_date"))),
        notes=str(form.get("notes", "")),
        items=items,
    )
    return RedirectResponse(f"/quotations/{quotation.id}", status_code=303)


@router.get("/{quotation_id}")
def quotation_detail(request: Request, quotation_id: int, db: DbSession, user: Proprietor):
    quotation = QuotationService(db).get(user, quotation_id)
    return templates.TemplateResponse(
        request,
        "quotations/detail.html",
        {"current_user": user, "quotation": quotation},
    )


@router.get("/{quotation_id}/pdf")
def download_pdf(quotation_id: int, db: DbSession, user: Proprietor):
    filename, pdf = QuotationService(db).render_pdf(user, quotation_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
