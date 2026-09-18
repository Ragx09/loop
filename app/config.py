"""Application configuration.

All environment-specific values are read from environment variables (or a local
.env file). Nothing here may contain real credentials — see .env.example.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LOOP"
    app_env: str = "development"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    api_url: str = "http://localhost:8000"

    # SQLAlchemy URL. PostgreSQL is the target database for every environment.
    database_url: str = "postgresql+psycopg://loop:loop@localhost:5432/loop"

    # Optional override used only by the automated test suite.
    test_database_url: str | None = None

    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720

    # Name of the cookie holding the access token for browser sessions.
    session_cookie_name: str = "loop_session"

    # --- Demo mode -------------------------------------------------------
    # Off everywhere except the public demo deployment. When off, the demo
    # sign-in options are not rendered and the demo endpoint does not exist.
    demo_mode: bool = False
    #: Password given to the seeded demo accounts. Only the seed command reads
    #: it; like every other credential it never appears in source.
    demo_password: str | None = None
    #: Wording of the strip shown to signed-in demo users.
    demo_reset_note: str = "Demo data — resets daily."

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (import this, never instantiate Settings directly)."""
    return Settings()
