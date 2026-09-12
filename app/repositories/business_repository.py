"""Data access for businesses."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business import Business


class BusinessRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, business_id: int) -> Business | None:
        return self.db.get(Business, business_id)

    def get_by_key(self, key: str) -> Business | None:
        stmt = select(Business).where(Business.key == key)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active(self) -> list[Business]:
        stmt = select(Business).where(Business.is_active.is_(True)).order_by(Business.name)
        return list(self.db.execute(stmt).scalars())

    def add(self, business: Business) -> Business:
        self.db.add(business)
        self.db.flush()
        return business
