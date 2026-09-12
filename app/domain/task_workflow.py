"""Task status workflow.

The workflow is declared as data, not as branching code, so new statuses or
transitions can be introduced later without rewriting the task module.
"""

from dataclasses import dataclass

from app.domain.enums import TaskStatus, UserRole

S = TaskStatus
R = UserRole


@dataclass(frozen=True)
class Transition:
    """A single allowed status change."""

    source: TaskStatus
    target: TaskStatus
    allowed_roles: frozenset[UserRole]
    #: Whether the task must have an assigned engineer for this transition.
    requires_assignee: bool = True


#: The currently supported workflow:
#: YET_TO_ASSIGN -> ASSIGNED -> IN_PROGRESS -> COMPLETED
TRANSITIONS: tuple[Transition, ...] = (
    Transition(S.YET_TO_ASSIGN, S.ASSIGNED, frozenset({R.PROPRIETOR})),
    Transition(S.ASSIGNED, S.IN_PROGRESS, frozenset({R.PROPRIETOR, R.SERVICE_ENGINEER})),
    Transition(S.IN_PROGRESS, S.COMPLETED, frozenset({R.PROPRIETOR, R.SERVICE_ENGINEER})),
)


def find_transition(source: TaskStatus, target: TaskStatus) -> Transition | None:
    for transition in TRANSITIONS:
        if transition.source is source and transition.target is target:
            return transition
    return None


def next_statuses(source: TaskStatus, role: UserRole) -> list[TaskStatus]:
    """Statuses a user with ``role`` may move a task in ``source`` status to."""
    return [t.target for t in TRANSITIONS if t.source is source and role in t.allowed_roles]


#: Statuses that can never appear in a given role's own task list. A service
#: engineer only ever sees tasks already assigned to them, so "Yet to Assign"
#: is not a filter they can ever match.
HIDDEN_STATUSES: dict[UserRole, frozenset[TaskStatus]] = {
    UserRole.SERVICE_ENGINEER: frozenset({S.YET_TO_ASSIGN}),
}


def visible_statuses(role: UserRole) -> list[TaskStatus]:
    """Statuses worth offering as list filters to a user with ``role``."""
    hidden = HIDDEN_STATUSES.get(role, frozenset())
    return [status for status in TaskStatus if status not in hidden]
