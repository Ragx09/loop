"""Data access for users."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_role(self, role: UserRole, active_only: bool = True) -> list[User]:
        stmt = select(User).where(User.role == role)
        if active_only:
            stmt = stmt.where(User.is_active.is_(True))
        return list(self.db.execute(stmt.order_by(User.full_name)).scalars())

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
