"""Demo mode.

Two things matter here: the demo must be invisible when it is switched off, and
when it is on it must not have loosened any authorization rule.
"""

import pytest
from sqlalchemy import func, select

from app.config import get_settings
from app.core.errors import ValidationError
from app.demo.accounts import DEMO_ACCOUNTS
from app.demo.seed import seed_demo
from app.models.business import Business
from app.models.quotation import Quotation
from app.models.task import Task
from app.models.user import User

DEMO_PASSWORD = "demo-password-not-a-real-secret"


@pytest.fixture()
def demo_mode(monkeypatch):
    """Turn demo mode on for one test, then put the settings back."""
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DEMO_PASSWORD", DEMO_PASSWORD)
    get_settings.cache_clear()
    yield
    monkeypatch.undo()
    get_settings.cache_clear()


@pytest.fixture()
def businesses(db):
    """Both quotation businesses, normally created by migration 0002/0003."""
    db.add_all(
        [
            Business(key="arcot_enterprises", name="Arcot Enterprises"),
            Business(key="arcot_automations", name="Arcot Automations"),
        ]
    )
    db.commit()


@pytest.fixture()
def demo_data(db, businesses, demo_mode):
    return seed_demo(db)


def _count(db, model) -> int:
    return db.execute(select(func.count()).select_from(model)).scalar_one()


# --- switched off ---------------------------------------------------------
def test_login_page_has_no_demo_options_by_default(client):
    body = client.get("/login").text
    assert "/login/demo" not in body
    # The ordinary sign-in form is untouched.
    assert 'action="/login"' in body


def test_demo_endpoint_does_not_exist_when_disabled(client):
    response = client.post("/login/demo", data={"account": "proprietor"})
    assert response.status_code == 404


def test_seeding_is_refused_when_demo_mode_is_off(db):
    with pytest.raises(ValidationError):
        seed_demo(db)


# --- switched on ----------------------------------------------------------
def test_login_page_offers_every_demo_account(client, demo_mode):
    body = client.get("/login").text
    for account in DEMO_ACCOUNTS:
        assert account.label in body
        assert f'value="{account.key}"' in body


def test_seed_requires_a_password(db, businesses, demo_mode, monkeypatch):
    monkeypatch.delenv("DEMO_PASSWORD")
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        seed_demo(db)


def test_seed_creates_sample_data(demo_data, db):
    assert demo_data.tasks > 0
    assert demo_data.quotations == 3
    assert _count(db, Task) == demo_data.tasks
    assert _count(db, Quotation) == 3
    for account in DEMO_ACCOUNTS:
        assert db.execute(
            select(User).where(User.username == account.username)
        ).scalar_one_or_none() is not None


def test_seed_is_idempotent(demo_data, db):
    before = (_count(db, User), _count(db, Task), _count(db, Quotation))
    seed_demo(db)
    assert (_count(db, User), _count(db, Task), _count(db, Quotation)) == before


def test_reset_returns_the_demo_to_the_same_clean_state(demo_data, db):
    before = (_count(db, User), _count(db, Task), _count(db, Quotation))
    seed_demo(db, reset=True)
    assert (_count(db, User), _count(db, Task), _count(db, Quotation)) == before


def test_demo_proprietor_signs_in_and_sees_the_launcher(client, demo_data):
    response = client.post(
        "/login/demo", data={"account": "proprietor"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert get_settings().session_cookie_name in response.cookies

    home = client.get("/")
    assert home.status_code == 200
    assert "Demo Proprietor" in home.text


def test_demo_engineer_lands_on_their_task_list(client, demo_data):
    response = client.post(
        "/login/demo", data={"account": "engineer"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    tasks = client.get("/tasks")
    assert tasks.status_code == 200
    # Their own jobs only: an unassigned task must not be visible to them.
    assert "Coastal Foods" not in tasks.text


def test_demo_engineer_is_still_blocked_from_quotations(client, demo_data):
    client.post("/login/demo", data={"account": "engineer"})
    assert client.get("/quotations").status_code == 403


def test_unknown_demo_account_is_rejected(client, demo_mode):
    response = client.post("/login/demo", data={"account": "administrator"})
    assert response.status_code == 401
    assert get_settings().session_cookie_name not in response.cookies


def test_demo_login_fails_gracefully_before_seeding(client, demo_mode):
    response = client.post("/login/demo", data={"account": "proprietor"})
    assert response.status_code == 401
    assert "not available" in response.text
