"""Data access for tasks."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import TaskStatus, TaskType
from app.models.task import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, task_id: int) -> Task | None:
        return self.db.get(Task, task_id)

    def list(
        self,
        *,
        status: TaskStatus | None = None,
        task_type: TaskType | None = None,
        assigned_engineer_id: int | None = None,
        scheduled_on: date | None = None,
    ) -> list[Task]:
        stmt = select(Task)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)
        if assigned_engineer_id is not None:
            stmt = stmt.where(Task.assigned_engineer_id == assigned_engineer_id)
        if scheduled_on is not None:
            stmt = stmt.where(Task.scheduled_date == scheduled_on)
        stmt = stmt.order_by(Task.scheduled_date.asc(), Task.created_at.desc())
        return list(self.db.execute(stmt).unique().scalars())

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task
