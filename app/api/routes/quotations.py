from fastapi import APIRouter, Response

from app.core.deps import DbSession, Proprietor
from app.schemas.quotation import (
    BusinessOut,
    QuotationCreate,
    QuotationOut,
    TemplateOut,
)
from app.services.quotation_service import QuotationService

router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.get("/businesses", response_model=list[BusinessOut])
def list_businesses(db: DbSession, _: Proprietor) -> list[BusinessOut]:
    return [BusinessOut.model_validate(b) for b in QuotationService(db).list_businesses()]


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(db: DbSession, _: Proprietor) -> list[TemplateOut]:
    return [
        TemplateOut(key=t.key, name=t.name, description=t.description)
        for t in QuotationService(db).list_templates()
    ]


@router.get("", response_model=list[QuotationOut])
def list_quotations(db: DbSession, user: Proprietor) -> list[QuotationOut]:
    return [QuotationOut.model_validate(q) for q in QuotationService(db).list_quotations(user)]


@router.post("", response_model=QuotationOut, status_code=201)
def create_quotation(
    payload: QuotationCreate, db: DbSession, user: Proprietor
) -> QuotationOut:
    data = payload.model_dump()
    items = data.pop("items")
    quotation = QuotationService(db).create_quotation(user, items=items, **data)
    return QuotationOut.model_validate(quotation)


@router.get("/{quotation_id}", response_model=QuotationOut)
def get_quotation(quotation_id: int, db: DbSession, user: Proprietor) -> QuotationOut:
    return QuotationOut.model_validate(QuotationService(db).get(user, quotation_id))


@router.get("/{quotation_id}/pdf")
def download_pdf(quotation_id: int, db: DbSession, user: Proprietor) -> Response:
    filename, pdf = QuotationService(db).render_pdf(user, quotation_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
