from fastapi import APIRouter

from app.web.routes import (
    auth,
    customers,
    dashboard,
    inventory,
    invoices,
    quotations,
    tasks,
)

web_router = APIRouter()
web_router.include_router(auth.router)
web_router.include_router(dashboard.router)
web_router.include_router(tasks.router)
web_router.include_router(customers.router)
web_router.include_router(quotations.router)
web_router.include_router(invoices.router)
web_router.include_router(inventory.router)
