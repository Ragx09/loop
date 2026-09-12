from fastapi import APIRouter

from app.web.routes import auth, quotations, tasks

web_router = APIRouter()
web_router.include_router(auth.router)
web_router.include_router(tasks.router)
web_router.include_router(quotations.router)
