"""The owner dashboard — proprietor only."""

from fastapi import APIRouter, Request

from app.core.deps import DbSession, Proprietor
from app.services.dashboard_service import DashboardService
from app.web.templating import templates

router = APIRouter(prefix="/dashboard", tags=["web"])


@router.get("")
def dashboard(request: Request, db: DbSession, user: Proprietor):
    return templates.TemplateResponse(
        request,
        "dashboard/overview.html",
        {"current_user": user, **DashboardService(db).overview(user)},
    )
