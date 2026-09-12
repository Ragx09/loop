"""Task pages. All rules live in TaskService; these routes only shape the UI."""

from datetime import date

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse

from app.core.deps import CurrentUser, DbSession
from app.domain.enums import TaskStatus, TaskType, UserRole
from app.domain.task_workflow import visible_statuses
from app.services.auth_service import AuthService
from app.services.task_service import TaskService
from app.web.templating import templates

router = APIRouter(prefix="/tasks", tags=["web"])


@router.get("")
def task_list(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    status: str | None = Query(default=None),
    task_type: str | None = Query(default=None),
):
    service = TaskService(db)
    selected_status = TaskStatus(status) if status else None
    selected_type = TaskType(task_type) if task_type else None
    tasks = service.list_for_user(user, status=selected_status, task_type=selected_type)
    statuses = visible_statuses(user.role)

    return templates.TemplateResponse(
        request,
        "tasks/list.html",
        {
            "current_user": user,
            "tasks": tasks,
            "selected_status": selected_status,
            "selected_type": selected_type,
            "statuses": statuses,
            "types": list(TaskType),
            "counts": _status_counts(service, user, statuses),
        },
    )


@router.get("/new")
def new_task_page(request: Request, db: DbSession, user: CurrentUser):
    engineers = AuthService(db).list_assignable(user) if user.role is UserRole.PROPRIETOR else []
    return templates.TemplateResponse(
        request,
        "tasks/new.html",
        {
            "current_user": user,
            "engineers": engineers,
            "types": list(TaskType),
            "today": date.today().isoformat(),
            "error": None,
        },
    )


@router.post("/new")
def create_task(
    db: DbSession,
    user: CurrentUser,
    task_type: str = Form(...),
    scheduled_date: date = Form(...),
    customer_name: str = Form(default=""),
    model: str = Form(default=""),
    meter_reading: str = Form(default=""),
    notes: str = Form(default=""),
    assigned_engineer_id: str = Form(default=""),
):
    task = TaskService(db).create_task(
        user,
        task_type=TaskType(task_type),
        scheduled_date=scheduled_date,
        customer_name=customer_name,
        model=model,
        meter_reading=meter_reading,
        notes=notes,
        assigned_engineer_id=int(assigned_engineer_id) if assigned_engineer_id else None,
    )
    return RedirectResponse(f"/tasks/{task.id}", status_code=303)


@router.get("/{task_id}")
def task_detail(request: Request, task_id: int, db: DbSession, user: CurrentUser):
    service = TaskService(db)
    task = service.get_for_user(user, task_id)
    engineers = AuthService(db).list_assignable(user) if user.role is UserRole.PROPRIETOR else []
    return templates.TemplateResponse(
        request,
        "tasks/detail.html",
        {
            "current_user": user,
            "task": task,
            "engineers": engineers,
            "actions": service.available_actions(user, task),
        },
    )


@router.post("/{task_id}/details")
def update_details(
    task_id: int,
    db: DbSession,
    user: CurrentUser,
    customer_name: str = Form(default=""),
    model: str = Form(default=""),
    meter_reading: str = Form(default=""),
    notes: str = Form(default=""),
    scheduled_date: date | None = Form(default=None),
):
    TaskService(db).update_details(
        user,
        task_id,
        customer_name=customer_name,
        model=model,
        meter_reading=meter_reading,
        notes=notes,
        scheduled_date=scheduled_date,
    )
    return RedirectResponse(f"/tasks/{task_id}", status_code=303)


@router.post("/{task_id}/assign")
def assign_task(
    task_id: int, db: DbSession, user: CurrentUser, engineer_id: int = Form(...)
):
    TaskService(db).assign(user, task_id, engineer_id, commit=True)
    return RedirectResponse(f"/tasks/{task_id}", status_code=303)


@router.post("/{task_id}/status")
def change_status(task_id: int, db: DbSession, user: CurrentUser, status: str = Form(...)):
    TaskService(db).change_status(user, task_id, TaskStatus(status))
    return RedirectResponse(f"/tasks/{task_id}", status_code=303)


def _status_counts(
    service: TaskService, user, statuses: list[TaskStatus]
) -> dict[TaskStatus, int]:
    """Counts per status, scoped to what the user is allowed to see."""
    all_tasks = service.list_for_user(user)
    return {status: sum(1 for t in all_tasks if t.status is status) for status in statuses}
