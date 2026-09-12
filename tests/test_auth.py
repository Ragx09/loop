"""Authentication and access control."""

import pytest

from tests.conftest import ENGINEER_PASSWORD, PROPRIETOR_PASSWORD, auth_headers, login


def test_proprietor_can_log_in(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["role"] == "PROPRIETOR"


def test_engineer_can_log_in(client, seeded):
    token = login(client, "eng1", ENGINEER_PASSWORD)
    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["role"] == "SERVICE_ENGINEER"


@pytest.mark.parametrize(
    ("username", "password"),
    [("owner", "wrong-password"), ("nobody", PROPRIETOR_PASSWORD)],
)
def test_bad_credentials_are_rejected_identically(client, seeded, username, password):
    response = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."


def test_api_requires_authentication(client, seeded):
    assert client.get("/api/tasks").status_code == 401


def test_invalid_token_is_rejected(client, seeded):
    response = client.get("/api/tasks", headers=auth_headers("not-a-real-token"))
    assert response.status_code == 401


def test_passwords_are_hashed_not_stored(seeded):
    proprietor = seeded["proprietor"]
    assert PROPRIETOR_PASSWORD not in proprietor.password_hash
    assert proprietor.password_hash.startswith("$2")
