from fastapi import APIRouter

from app.core.deps import DbSession, Proprietor
from app.schemas.auth import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/engineers", response_model=list[UserOut])
def list_engineers(db: DbSession, _: Proprietor) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in AuthService(db).list_engineers()]


@router.get("/assignable", response_model=list[UserOut])
def list_assignable(db: DbSession, user: Proprietor) -> list[UserOut]:
    """Everyone a task may be handed to, including the proprietor themselves."""
    return [UserOut.model_validate(u) for u in AuthService(db).list_assignable(user)]
