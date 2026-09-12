"""Task business logic.

Every method takes the acting user and enforces authorization here — the
transport layers (API and web) must not implement their own rules.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.domain.enums import TaskStatus, TaskType, UserRole
from app.domain.task_workflow import find_transition, next_statuses
from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = TaskRepository(db)
        self.users = UserRepository(db)

    # --- reads -----------------------------------------------------------
    def list_for_user(
        self,
        actor: User,
        *,
        status: TaskStatus | None = None,
        task_type: TaskType | None = None,
        scheduled_on: date | None = None,
    ) -> list[Task]:
        """Proprietors see every task; engineers only see their own."""
        assigned_engineer_id = None if actor.role is UserRole.PROPRIETOR else actor.id
        return self.tasks.list(
            status=status,
            task_type=task_type,
            assigned_engineer_id=assigned_engineer_id,
            scheduled_on=scheduled_on,
        )

    def list_today(self, actor: User) -> list[Task]:
        """Tasks scheduled for today, scoped to what the actor may see."""
        return self.list_for_user(actor, scheduled_on=date.today())

    def get_for_user(self, actor: User, task_id: int) -> Task:
        task = self.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task not found.")
        self._assert_can_view(actor, task)
        return task

    def available_actions(self, actor: User, task: Task) -> list[TaskStatus]:
        """Status transitions the actor may currently perform on the task."""
        actions = []
        for target in next_statuses(task.status, actor.role):
            transition = find_transition(task.status, target)
            if transition is None:
                continue
            if transition.requires_assignee and task.assigned_engineer_id is None:
                continue
            actions.append(target)
        return actions

    # --- writes ----------------------------------------------------------
    def create_task(
        self,
        actor: User,
        *,
        task_type: TaskType,
        scheduled_date: date,
        customer_name: str | None = None,
        model: str | None = None,
        meter_reading: str | None = None,
        notes: str | None = None,
        assigned_engineer_id: int | None = None,
    ) -> Task:
        self._assert_proprietor(actor)
        if scheduled_date is None:
            raise ValidationError("Scheduled date is required.")

        task = Task(
            task_type=task_type,
            status=TaskStatus.YET_TO_ASSIGN,
            scheduled_date=scheduled_date,
            customer_name=_clean(customer_name),
            model=_clean(model),
            meter_reading=_clean(meter_reading),
            notes=_clean(notes),
            created_by_id=actor.id,
        )
        self.tasks.add(task)

        # Assigning during creation is a convenience; it reuses the same rules.
        if assigned_engineer_id is not None:
            self.assign(actor, task.id, assigned_engineer_id)

        self.db.commit()
        self.db.refresh(task)
        return task

    def assign(self, actor: User, task_id: int, engineer_id: int, commit: bool = False) -> Task:
        self._assert_proprietor(actor)
        task = self.get_for_user(actor, task_id)

        assignee = self.users.get(engineer_id)
        if assignee is None or not self._is_assignable(actor, assignee):
            raise ValidationError("Select a valid service engineer.")
        if not assignee.is_active:
            raise ValidationError("That service engineer is no longer active.")
        if task.status is TaskStatus.COMPLETED:
            raise ValidationError("A completed task cannot be reassigned.")

        task.assigned_engineer_id = assignee.id
        if task.status is TaskStatus.YET_TO_ASSIGN:
            task.status = TaskStatus.ASSIGNED

        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(task)
        return task

    def update_details(
        self,
        actor: User,
        task_id: int,
        *,
        customer_name: str | None = None,
        model: str | None = None,
        meter_reading: str | None = None,
        notes: str | None = None,
        scheduled_date: date | None = None,
    ) -> Task:
        """Update task information.

        Engineers may update the details of their own tasks; only the proprietor
        may change the scheduled date.
        """
        task = self.get_for_user(actor, task_id)
        if task.status is TaskStatus.COMPLETED:
            raise ValidationError("A completed task can no longer be edited.")

        if actor.role is UserRole.SERVICE_ENGINEER and task.assigned_engineer_id != actor.id:
            raise PermissionDeniedError("This task is not assigned to you.")

        if customer_name is not None:
            task.customer_name = _clean(customer_name)
        if model is not None:
            task.model = _clean(model)
        if meter_reading is not None:
            task.meter_reading = _clean(meter_reading)
        if notes is not None:
            task.notes = _clean(notes)

        if scheduled_date is not None:
            self._assert_proprietor(actor, "Only the proprietor can change the scheduled date.")
            task.scheduled_date = scheduled_date

        self.db.commit()
        self.db.refresh(task)
        return task

    def change_status(self, actor: User, task_id: int, target: TaskStatus) -> Task:
        task = self.get_for_user(actor, task_id)

        transition = find_transition(task.status, target)
        if transition is None:
            raise ValidationError(
                f"A task cannot move from {task.status.label} to {target.label}."
            )
        if actor.role not in transition.allowed_roles:
            raise PermissionDeniedError("You are not allowed to perform this action.")
        if transition.requires_assignee and task.assigned_engineer_id is None:
            raise ValidationError("Assign an engineer before progressing this task.")
        if actor.role is UserRole.SERVICE_ENGINEER and task.assigned_engineer_id != actor.id:
            raise PermissionDeniedError("This task is not assigned to you.")

        task.status = target
        self.db.commit()
        self.db.refresh(task)
        return task

    # --- authorization helpers -------------------------------------------
    @staticmethod
    def _is_assignable(actor: User, candidate: User) -> bool:
        """Who a task may be handed to.

        Service engineers are always assignable. The proprietor may also take a
        task on themselves ("assign to myself") — but never hand one to another
        proprietor, which would be an administrative change, not a work handover.
        """
        if candidate.role is UserRole.SERVICE_ENGINEER:
            return True
        return candidate.id == actor.id

    @staticmethod
    def _assert_proprietor(actor: User, message: str = "Only the proprietor can do this.") -> None:
        if actor.role is not UserRole.PROPRIETOR:
            raise PermissionDeniedError(message)

    @staticmethod
    def _assert_can_view(actor: User, task: Task) -> None:
        if actor.role is UserRole.PROPRIETOR:
            return
        if task.assigned_engineer_id != actor.id:
            raise PermissionDeniedError("This task is not assigned to you.")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
