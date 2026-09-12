from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Business(TimestampMixin, Base):
    """A business name under which quotations are issued.

    Currently: Arcot Enterprises and Arcot Automations. Stored as data (not code)
    so further businesses can be added without a code change. The contact fields
    are optional placeholders filled in when the real quotation formats arrive.
    """

    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    #: Stable machine key used by templates and APIs, e.g. "arcot_enterprises".
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Business {self.key}>"
