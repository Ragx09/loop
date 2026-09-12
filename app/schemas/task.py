from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TaskStatus, TaskType
from app.schemas.auth import UserOut


class TaskCreate(BaseModel):
    task_type: TaskType
    scheduled_date: date
    customer_name: str | None = Field(default=None, max_length=160)
    model: str | None = Field(default=None, max_length=120)
    meter_reading: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=1000)
    assigned_engineer_id: int | None = None


class TaskUpdate(BaseModel):
    """Partial update. Only the supplied fields are changed."""

    customer_name: str | None = Field(default=None, max_length=160)
    model: str | None = Field(default=None, max_length=120)
    meter_reading: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=1000)
    scheduled_date: date | None = None


class TaskAssign(BaseModel):
    engineer_id: int


class TaskStatusChange(BaseModel):
    status: TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: TaskType
    status: TaskStatus
    scheduled_date: date
    customer_name: str | None
    model: str | None
    meter_reading: str | None
    notes: str | None
    created_at: datetime
    assigned_engineer: UserOut | None
