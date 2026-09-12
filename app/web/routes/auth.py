from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.core.deps import DbSession, OptionalUser
from app.core.errors import AuthenticationError
from app.domain.enums import UserRole
from app.services.auth_service import AuthService
from app.services.task_service import TaskService
from app.web.templating import templates
from app.web.tools import tools_for

router = APIRouter(tags=["web"])


@router.get("/")
def home(request: Request, db: DbSession, user: OptionalUser):
    """The proprietor's tool launcher. Engineers go straight to their tasks."""
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role is not UserRole.PROPRIETOR:
        return RedirectResponse("/tasks", status_code=303)

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "current_user": user,
            "tools": tools_for(user.role),
            "today_tasks": TaskService(db).list_today(user),
        },
    )


@router.get("/login")
def login_page(request: Request, user: OptionalUser):
    if user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request, "auth/login.html", {"current_user": None, "error": None}
    )


@router.post("/login")
def login_submit(
    request: Request,
    db: DbSession,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
):
    settings = get_settings()
    try:
        _, token = AuthService(db).login(username, password)
    except AuthenticationError as exc:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"current_user": None, "error": exc.message},
            status_code=401,
        )

    target = next if next.startswith("/") and not next.startswith("//") else "/"
    response = RedirectResponse(target, status_code=303)
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(get_settings().session_cookie_name)
    return response
