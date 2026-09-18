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


class InvoiceStatus(str, Enum):
    """Derived from payments received, never set by hand — see InvoiceService."""

    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"

    @property
    def label(self) -> str:
        return {
            "PENDING": "Pending",
            "PARTIALLY_PAID": "Partially Paid",
            "PAID": "Paid",
            "OVERDUE": "Overdue",
        }[self.value]


class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    UPI = "UPI"
    CHEQUE = "CHEQUE"
    CARD = "CARD"

    @property
    def label(self) -> str:
        return {
            "CASH": "Cash",
            "BANK_TRANSFER": "Bank Transfer",
            "UPI": "UPI",
            "CHEQUE": "Cheque",
            "CARD": "Card",
        }[self.value]
