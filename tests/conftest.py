"""Test fixtures.

Tests run against TEST_DATABASE_URL when it is set (use a PostgreSQL URL to test
against the real target database). When it is not set they fall back to an
isolated SQLite file so the suite can always run without a server. The schema
uses only portable column types, so both behave identically for these tests.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_DB_URL = os.getenv("TEST_DATABASE_URL") or "sqlite+pysqlite:///./loop_test.sqlite3"
# Must be set before the app imports its settings.
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["JWT_SECRET"] = "test-secret-not-used-in-any-real-environment"

from app.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.domain.enums import UserRole  # noqa: E402
from app.main import app  # noqa: E402
from app.models.business import Business  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402

get_settings.cache_clear()

engine = create_engine(TEST_DB_URL, future=True)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

PROPRIETOR_PASSWORD = "proprietor-pass-1"
ENGINEER_PASSWORD = "engineer-pass-1"


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def seeded(db):
    """A proprietor, two engineers and the two businesses."""
    auth = AuthService(db)
    proprietor = auth.create_user(
        username="owner",
        full_name="Owner",
        role=UserRole.PROPRIETOR,
        password=PROPRIETOR_PASSWORD,
    )
    engineer_one = auth.create_user(
        username="eng1",
        full_name="Engineer One",
        role=UserRole.SERVICE_ENGINEER,
        password=ENGINEER_PASSWORD,
    )
    engineer_two = auth.create_user(
        username="eng2",
        full_name="Engineer Two",
        role=UserRole.SERVICE_ENGINEER,
        password=ENGINEER_PASSWORD,
    )
    business = Business(key="arcot_enterprises", name="Arcot Enterprises")
    db.add(business)
    db.commit()
    return {
        "proprietor": proprietor,
        "engineer_one": engineer_one,
        "engineer_two": engineer_two,
        "business": business,
    }


@pytest.fixture()
def client(db):
    """TestClient sharing the test session, so API and fixtures see one database."""

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
