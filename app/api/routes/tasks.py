from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.domain.enums import TaskStatus, TaskType
from app.schemas.task import TaskAssign, TaskCreate, TaskOut, TaskStatusChange, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    db: DbSession,
    user: CurrentUser,
    status: TaskStatus | None = Query(default=None),
    task_type: TaskType | None = Query(default=None),
) -> list[TaskOut]:
    tasks = TaskService(db).list_for_user(user, status=status, task_type=task_type)
    return [TaskOut.model_validate(t) for t in tasks]


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: DbSession, user: CurrentUser) -> TaskOut:
    task = TaskService(db).create_task(user, **payload.model_dump())
    return TaskOut.model_validate(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: DbSession, user: CurrentUser) -> TaskOut:
    return TaskOut.model_validate(TaskService(db).get_for_user(user, task_id))


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, payload: TaskUpdate, db: DbSession, user: CurrentUser
) -> TaskOut:
    task = TaskService(db).update_details(
        user, task_id, **payload.model_dump(exclude_unset=True)
    )
    return TaskOut.model_validate(task)


@router.post("/{task_id}/assign", response_model=TaskOut)
def assign_task(
    task_id: int, payload: TaskAssign, db: DbSession, user: CurrentUser
) -> TaskOut:
    task = TaskService(db).assign(user, task_id, payload.engineer_id, commit=True)
    return TaskOut.model_validate(task)


@router.post("/{task_id}/status", response_model=TaskOut)
def change_status(
    task_id: int, payload: TaskStatusChange, db: DbSession, user: CurrentUser
) -> TaskOut:
    task = TaskService(db).change_status(user, task_id, payload.status)
    return TaskOut.model_validate(task)
