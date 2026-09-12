"""Data access for quotations."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.quotation import Quotation


class QuotationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, quotation_id: int) -> Quotation | None:
        return self.db.get(Quotation, quotation_id)

    def list(self) -> list[Quotation]:
        stmt = select(Quotation).order_by(Quotation.created_at.desc())
        return list(self.db.execute(stmt).unique().scalars())

    def count_for_year(self, business_id: int, year: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Quotation)
            .where(
                Quotation.business_id == business_id,
                Quotation.quotation_date >= date(year, 1, 1),
                Quotation.quotation_date <= date(year, 12, 31),
            )
        )
        return int(self.db.execute(stmt).scalar_one())

    def add(self, quotation: Quotation) -> Quotation:
        self.db.add(quotation)
        self.db.flush()
        return quotation
