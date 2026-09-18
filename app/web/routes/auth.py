from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.core.deps import DbSession, OptionalUser
from app.core.errors import AuthenticationError
from app.demo.accounts import demo_accounts
from app.domain.enums import UserRole
from app.services.auth_service import AuthService
from app.services.demo_service import DemoService
from app.services.task_service import TaskService
from app.web.templating import templates
from app.web.tools import tools_for

router = APIRouter(tags=["web"])


def _set_session_cookie(response: Response, token: str) -> None:
    """The one place a browser session is established."""
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.access_token_expire_minutes * 60,
    )


def _login_page(request: Request, error: str | None = None, status_code: int = 200):
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"current_user": None, "error": error, "demo_accounts": demo_accounts()},
        status_code=status_code,
    )


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
    return _login_page(request)


@router.post("/login")
def login_submit(
    request: Request,
    db: DbSession,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/"),
):
    try:
        _, token = AuthService(db).login(username, password)
    except AuthenticationError as exc:
        return _login_page(request, error=exc.message, status_code=401)

    target = next if next.startswith("/") and not next.startswith("//") else "/"
    response = RedirectResponse(target, status_code=303)
    _set_session_cookie(response, token)
    return response


@router.post("/login/demo")
def login_demo(request: Request, db: DbSession, account: str = Form(...)):
    """One-click sign-in as a demo persona.

    Raises NotFoundError (404) when demo mode is off, so this route is invisible
    on the real instance whether or not the button is rendered.
    """
    try:
        _, token = DemoService(db).login(account)
    except AuthenticationError as exc:
        return _login_page(request, error=exc.message, status_code=401)

    # Always "/": home() already sends engineers on to their task list.
    response = RedirectResponse("/", status_code=303)
    _set_session_cookie(response, token)
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(get_settings().session_cookie_name)
    return response
