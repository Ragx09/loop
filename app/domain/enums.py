"""Domain enumerations.

These values are persisted in the database, so the *values* are part of the
schema. Labels are UI concerns and kept alongside for a single source of truth.
"""

from enum import Enum


class UserRole(str, Enum):
    PROPRIETOR = "PROPRIETOR"
    SERVICE_ENGINEER = "SERVICE_ENGINEER"

    @property
    def label(self) -> str:
        return {"PROPRIETOR": "Proprietor", "SERVICE_ENGINEER": "Service Engineer"}[self.value]


class TaskType(str, Enum):
    SERVICE_CALL = "SERVICE_CALL"
    SEND_MATERIAL = "SEND_MATERIAL"

    @property
    def label(self) -> str:
        return {"SERVICE_CALL": "Service Call", "SEND_MATERIAL": "Sending Material"}[self.value]


class TaskStatus(str, Enum):
    YET_TO_ASSIGN = "YET_TO_ASSIGN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

    @property
    def label(self) -> str:
        return {
            "YET_TO_ASSIGN": "Yet to Assign",
            "ASSIGNED": "Assigned",
            "IN_PROGRESS": "In Progress",
            "COMPLETED": "Completed",
        }[self.value]
