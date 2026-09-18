from datetime import date

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.enums import TaskStatus, TaskType


class Task(TimestampMixin, Base):
    """A unit of work created by the proprietor after a customer call."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    task_type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TaskStatus.YET_TO_ASSIGN,
        index=True,
    )

    #: Date on which the task should be carried out (chosen by the proprietor).
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Task details. Optional at creation time: the proprietor may only learn some
    # of them later, and the service engineer fills them in while working.
    customer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    meter_reading: Mapped[str | None] = mapped_column(String(60), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Optional links to the CRM. The free-text fields above are kept and still
    # work on their own, so every task created before customers existed is
    # unaffected; attaching a customer later is purely additive.
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True, index=True
    )

    assigned_engineer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    assigned_engineer: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="assigned_tasks", foreign_keys=[assigned_engineer_id], lazy="joined"
    )
    created_by: Mapped["User"] = relationship(  # noqa: F821
        foreign_keys=[created_by_id], lazy="joined"
    )
    customer: Mapped["Customer | None"] = relationship(lazy="joined")  # noqa: F821
    equipment: Mapped["Equipment | None"] = relationship(lazy="joined")  # noqa: F821
    materials: Mapped[list["MaterialUsed"]] = relationship(  # noqa: F821
        cascade="all, delete-orphan", lazy="selectin"
    )
    report: Mapped["ServiceReport | None"] = relationship(  # noqa: F821
        back_populates="task", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_tasks_status_scheduled_date", "status", "scheduled_date"),
    )

    # --- Display helpers (derived, never stored) -------------------------
    @property
    def created_date(self) -> date:
        return self.created_at.date()

    @property
    def created_time(self):
        return self.created_at.time()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Task #{self.id} {self.task_type.value} {self.status.value}>"
