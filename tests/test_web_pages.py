"""Smoke tests for the server-rendered pages.

The pages take their stylesheets, brand wording and navigation from the UI
configuration modules rather than from the templates, so these tests check that
wiring end to end: the shell renders, and each role is offered exactly the
links it is allowed to see.
"""

from tests.conftest import ENGINEER_PASSWORD, PROPRIETOR_PASSWORD


def sign_in(client, username: str, password: str) -> None:
    """Log in through the browser form, leaving the session cookie on the client."""
    response = client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text


def test_login_page_renders_brand(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "LOOP" in response.text
    assert "/static/theme.css" in response.text
    assert "/static/app.css" in response.text


def test_signed_out_visitor_is_sent_to_login(client):
    response = client.get("/tasks", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_home_shows_proprietor_navigation_and_tools(client, seeded):
    sign_in(client, "owner", PROPRIETOR_PASSWORD)
    response = client.get("/")
    assert response.status_code == 200
    for link in ('href="/tasks"', 'href="/tasks/new"', 'href="/quotations"'):
        assert link in response.text
    assert "Generate Quotation" in response.text


def test_engineer_sees_only_their_own_navigation(client, seeded):
    sign_in(client, "eng1", ENGINEER_PASSWORD)
    response = client.get("/tasks")
    assert response.status_code == 200
    assert 'href="/quotations"' not in response.text
    assert 'href="/tasks/new"' not in response.text


def test_engineer_home_redirects_to_tasks(client, seeded):
    sign_in(client, "eng1", ENGINEER_PASSWORD)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/tasks"


def test_proprietor_pages_render(client, seeded):
    sign_in(client, "owner", PROPRIETOR_PASSWORD)
    for path in ("/tasks", "/tasks/new", "/quotations", "/quotations/new"):
        assert client.get(path).status_code == 200, path


def test_quotation_pages_are_closed_to_engineers(client, seeded):
    sign_in(client, "eng1", ENGINEER_PASSWORD)
    response = client.get("/quotations", follow_redirects=False)
    assert response.status_code == 403
