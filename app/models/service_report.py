from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ServiceReport(Base, TimestampMixin):
    """The record of what was done on a job, written when it is completed.

    One per task. The materials it lists are the MaterialUsed rows on the task,
    not a copy of them, so the report and the stock movements cannot disagree.
    """

    __tablename__ = "service_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    work_performed: Mapped[str] = mapped_column(String(2000), nullable=False)
    meter_reading: Mapped[str | None] = mapped_column(String(60), nullable=True)
    #: Typed, not drawn: a name is enough for a demo and needs no file storage.
    customer_signature: Mapped[str | None] = mapped_column(String(160), nullable=True)

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    task: Mapped["Task"] = relationship(lazy="joined")  # noqa: F821
    created_by: Mapped["User"] = relationship(lazy="joined")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ServiceReport task={self.task_id}>"
