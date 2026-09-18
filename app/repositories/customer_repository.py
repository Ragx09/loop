"""Data access for customers and their equipment."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer, Equipment


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, customer_id: int) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def list(self, search: str | None = None, active_only: bool = True) -> list[Customer]:
        stmt = select(Customer)
        if active_only:
            stmt = stmt.where(Customer.is_active.is_(True))
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(Customer.name.ilike(like))
        return list(self.db.execute(stmt.order_by(Customer.name)).scalars())

    def add(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.flush()
        return customer

    # --- equipment -------------------------------------------------------
    def get_equipment(self, equipment_id: int) -> Equipment | None:
        return self.db.get(Equipment, equipment_id)

    def add_equipment(self, equipment: Equipment) -> Equipment:
        self.db.add(equipment)
        self.db.flush()
        return equipment
