from fastapi import APIRouter, Response

from app.config import get_settings
from app.core.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> TokenResponse:
    settings = get_settings()
    _, token = AuthService(db).login(payload.username, payload.password)
    # Also set the cookie so the browser UI and the API share one session.
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(get_settings().session_cookie_name)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
