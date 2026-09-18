"""Signing in as a demo persona.

This is a shortcut through the sign-in *form*, not through authentication. The
token is issued by AuthService exactly as it is for a typed password, and the
user it belongs to is an ordinary user row with an ordinary role, so every
authorization rule in the application applies to demo visitors unchanged.
"""

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import AuthenticationError, NotFoundError
from app.demo.accounts import get_demo_account
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


class DemoService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.auth = AuthService(db)

    def login(self, account_key: str) -> tuple[User, str]:
        # Not enabled: the endpoint should look as though it does not exist,
        # rather than hinting that a demo door is there but shut.
        if not get_settings().demo_mode:
            raise NotFoundError("Not found.")

        account = get_demo_account((account_key or "").strip())
        if account is None:
            raise AuthenticationError("Unknown demo account.")

        user = self.users.get_by_username(account.username)
        if user is None or not user.is_active:
            # The demo database has not been seeded (or was reset mid-request).
            raise AuthenticationError(
                "The demo is not available right now. Please try again shortly."
            )

        return user, self.auth.issue_token(user)
