"""Shared FastAPI dependencies: session access and the current user.

The role is always re-read from the database — a role claim sent by a client is
never trusted.
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.domain.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository

DbSession = Annotated[Session, Depends(get_db)]


def extract_token(request: Request) -> str | None:
    """Accept either a browser session cookie or an Authorization header."""
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return request.cookies.get(get_settings().session_cookie_name)


def get_current_user(request: Request, db: DbSession) -> User:
    token = extract_token(request)
    if not token:
        raise AuthenticationError("Please sign in to continue.")

    payload = decode_access_token(token)
    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError) as exc:
        raise AuthenticationError("Your session is invalid or has expired.") from exc

    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Your session is no longer valid.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_proprietor(user: CurrentUser) -> User:
    if user.role is not UserRole.PROPRIETOR:
        raise PermissionDeniedError("Only the proprietor can access this.")
    return user


Proprietor = Annotated[User, Depends(require_proprietor)]


def get_optional_user(request: Request, db: DbSession) -> User | None:
    """Never raises — used by pages that render differently when signed out."""
    try:
        return get_current_user(request, db)
    except AuthenticationError:
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
