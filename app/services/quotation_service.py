"""Quotation business logic.

The service owns validation, persistence and authorization. Layout/PDF concerns
live entirely in app.quotation.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.domain.enums import UserRole
from app.models.business import Business
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User
from app.quotation.document import BusinessInfo, QuotationDocument, QuotationLine
from app.quotation.registry import QuotationTemplate, get_template, list_templates
from app.quotation.renderer import QuotationRenderer
from app.repositories.business_repository import BusinessRepository
from app.repositories.quotation_repository import QuotationRepository


class QuotationService:
    def __init__(self, db: Session, renderer: QuotationRenderer | None = None):
        self.db = db
        self.quotations = QuotationRepository(db)
        self.businesses = BusinessRepository(db)
        self._renderer = renderer

    @property
    def renderer(self) -> QuotationRenderer:
        # Built lazily: listing quotations should not pay for the PDF engine.
        if self._renderer is None:
            self._renderer = QuotationRenderer()
        return self._renderer

    # --- reads -----------------------------------------------------------
    def list_businesses(self) -> list[Business]:
        return self.businesses.list_active()

    def list_templates(self) -> list[QuotationTemplate]:
        return list_templates()

    def list_quotations(self, actor: User) -> list[Quotation]:
        self._assert_proprietor(actor)
        return self.quotations.list()

    def get(self, actor: User, quotation_id: int) -> Quotation:
        self._assert_proprietor(actor)
        quotation = self.quotations.get(quotation_id)
        if quotation is None:
            raise NotFoundError("Quotation not found.")
        return quotation

    # --- writes ----------------------------------------------------------
    def create_quotation(
        self,
        actor: User,
        *,
        business_id: int,
        template_key: str,
        customer_name: str,
        items: list[dict],
        quotation_date: date | None = None,
        quotation_number: str | None = None,
        customer_address: str | None = None,
        notes: str | None = None,
    ) -> Quotation:
        self._assert_proprietor(actor)

        business = self.businesses.get(business_id)
        if business is None or not business.is_active:
            raise ValidationError("Select a valid business.")
        get_template(template_key)  # raises for an unknown format

        customer_name = (customer_name or "").strip()
        if not customer_name:
            raise ValidationError("Customer name is required.")

        quotation_date = quotation_date or date.today()
        parsed_items = self._parse_items(items)

        quotation = Quotation(
            quotation_number=(quotation_number or "").strip()
            or self._next_quotation_number(business, quotation_date),
            quotation_date=quotation_date,
            business_id=business.id,
            template_key=template_key,
            customer_name=customer_name,
            customer_address=(customer_address or "").strip() or None,
            notes=(notes or "").strip() or None,
            created_by_id=actor.id,
            items=parsed_items,
        )
        self.quotations.add(quotation)
        self.db.commit()
        self.db.refresh(quotation)
        return quotation

    # --- rendering -------------------------------------------------------
    def build_document(self, quotation: Quotation) -> QuotationDocument:
        business = quotation.business
        return QuotationDocument(
            business=BusinessInfo(
                key=business.key,
                name=business.name,
                address=business.address,
                phone=business.phone,
                email=business.email,
                gstin=business.gstin,
            ),
            quotation_number=quotation.quotation_number,
            quotation_date=quotation.quotation_date,
            customer_name=quotation.customer_name,
            customer_address=quotation.customer_address,
            notes=quotation.notes,
            lines=[
                QuotationLine(
                    particulars=item.particulars,
                    hsn_code=item.hsn_code,
                    price=Decimal(item.price),
                    quantity=item.quantity,
                )
                for item in quotation.items
            ],
        )

    def render_pdf(self, actor: User, quotation_id: int) -> tuple[str, bytes]:
        """Returns (filename, pdf_bytes)."""
        quotation = self.get(actor, quotation_id)
        document = self.build_document(quotation)
        pdf = self.renderer.render_pdf(document, quotation.template_key)
        safe_number = "".join(
            c if c.isalnum() or c in "-_" else "-" for c in quotation.quotation_number
        )
        return f"quotation-{safe_number}.pdf", pdf

    # --- helpers ---------------------------------------------------------
    def _parse_items(self, items: list[dict]) -> list[QuotationItem]:
        parsed: list[QuotationItem] = []
        for position, raw in enumerate(items or []):
            particulars = (raw.get("particulars") or "").strip()
            raw_price = raw.get("price")
            hsn_code = (raw.get("hsn_code") or "").strip() or None

            # Skip completely empty rows: the entry form always renders blanks.
            if not particulars and raw_price in (None, "") and not hsn_code:
                continue
            if not particulars:
                raise ValidationError("Every quotation line needs particulars.")
            parsed.append(
                QuotationItem(
                    position=position,
                    particulars=particulars,
                    hsn_code=hsn_code,
                    price=_parse_price(raw_price),
                    quantity=_parse_quantity(raw.get("quantity")),
                )
            )

        if not parsed:
            raise ValidationError("Add at least one quotation line.")
        return parsed

    def _next_quotation_number(self, business: Business, on_date: date) -> str:
        """Fallback number when the proprietor does not supply one."""
        prefix = "".join(part[0] for part in business.name.split() if part)[:3].upper() or "QT"
        sequence = self.quotations.count_for_year(business.id, on_date.year) + 1
        return f"{prefix}/{on_date.year}/{sequence:04d}"

    @staticmethod
    def _assert_proprietor(actor: User) -> None:
        if actor.role is not UserRole.PROPRIETOR:
            raise PermissionDeniedError("Only the proprietor can manage quotations.")


def _parse_price(value) -> Decimal:
    if value in (None, ""):
        raise ValidationError("Every quotation line needs a price.")
    try:
        price = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("Price must be a number.") from exc
    if price < 0:
        raise ValidationError("Price cannot be negative.")
    return price.quantize(Decimal("0.01"))


def _parse_quantity(value) -> int:
    """Quantity defaults to 1 so older callers and blank fields keep working."""
    if value in (None, ""):
        return 1
    try:
        quantity = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError("Quantity must be a whole number.") from exc
    if quantity < 1:
        raise ValidationError("Quantity must be at least 1.")
    return quantity
