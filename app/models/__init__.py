"""SQLAlchemy models. Importing this package registers every table on Base."""

from app.models.business import Business
from app.models.customer import Customer, Equipment
from app.models.inventory import InventoryItem, MaterialUsed
from app.models.invoice import Invoice, InvoiceItem, Payment
from app.models.quotation import Quotation, QuotationItem
from app.models.service_report import ServiceReport
from app.models.task import Task
from app.models.user import User

__all__ = [
    "Business",
    "Customer",
    "Equipment",
    "InventoryItem",
    "Invoice",
    "InvoiceItem",
    "MaterialUsed",
    "Payment",
    "Quotation",
    "QuotationItem",
    "ServiceReport",
    "Task",
    "User",
]
