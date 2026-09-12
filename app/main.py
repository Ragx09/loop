"""FastAPI application entry point.

Two transport layers are mounted on one application:
  * /api/...  JSON REST API
  * /...      server-rendered pages for day-to-day use
Both delegate to the same services, so authorization cannot drift between them.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import get_settings
from app.core.errors import AuthenticationError, LoopError
from app.web.router import web_router
from app.web.templating import templates

logger = logging.getLogger("loop")
settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(api_router)
app.include_router(web_router)


def _wants_json(request: Request) -> bool:
    return request.url.path.startswith("/api") or "application/json" in request.headers.get(
        "accept", ""
    )


@app.exception_handler(LoopError)
def handle_loop_error(request: Request, exc: LoopError):
    """Expected errors: shown to the user, never leaking internals."""
    if _wants_json(request):
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code)

    if isinstance(exc, AuthenticationError):
        return RedirectResponse(f"/login?next={request.url.path}", status_code=303)

    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": exc.message, "status_code": exc.status_code, "current_user": None},
        status_code=exc.status_code,
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
