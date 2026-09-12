"""Authentication and user administration logic."""

from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User:
        user = self.users.get_by_username(username.strip().lower())
        # Same message for unknown user, wrong password and disabled account:
        # never reveal which usernames exist.
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password.")
        if not user.is_active:
            raise AuthenticationError("Invalid username or password.")
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id), role=user.role.value)

    def login(self, username: str, password: str) -> tuple[User, str]:
        user = self.authenticate(username, password)
        return user, self.issue_token(user)

    def create_user(
        self, *, username: str, full_name: str, role: UserRole, password: str
    ) -> User:
        username = username.strip().lower()
        if not username:
            raise ValidationError("Username is required.")
        if not full_name.strip():
            raise ValidationError("Full name is required.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if self.users.get_by_username(username) is not None:
            raise ValidationError(f"Username {username} already exists.")

        user = User(
            username=username,
            full_name=full_name.strip(),
            role=role,
            password_hash=hash_password(password),
            is_active=True,
        )
        return self.users.add(user)

    def list_engineers(self) -> list[User]:
        return self.users.list_by_role(UserRole.SERVICE_ENGINEER)

    def list_assignable(self, actor: User) -> list[User]:
        """Users a task may be assigned to, from ``actor``'s point of view.

        The proprietor comes first so "assign to myself" is the nearest option;
        engineers follow. Mirrors TaskService._is_assignable, which enforces it.
        """
        engineers = self.list_engineers()
        if actor.role is UserRole.PROPRIETOR:
            return [actor, *engineers]
        return engineers
