"""Task creation, assignment, workflow and authorization."""

from datetime import date, timedelta

from tests.conftest import ENGINEER_PASSWORD, PROPRIETOR_PASSWORD, auth_headers, login

NEXT_TUESDAY = (date.today() + timedelta(days=7)).isoformat()


def create_task(client, token, **overrides):
    payload = {
        "task_type": "SERVICE_CALL",
        "scheduled_date": NEXT_TUESDAY,
        "customer_name": "Kumar Traders",
    }
    payload.update(overrides)
    response = client.post("/api/tasks", json=payload, headers=auth_headers(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_proprietor_creates_task_with_automatic_created_timestamp(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, token)

    assert task["status"] == "YET_TO_ASSIGN"
    assert task["task_type"] == "SERVICE_CALL"
    assert task["scheduled_date"] == NEXT_TUESDAY
    assert task["created_at"] is not None
    assert task["assigned_engineer"] is None


def test_both_task_types_can_be_created(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    assert create_task(client, token, task_type="SEND_MATERIAL")["task_type"] == "SEND_MATERIAL"
    assert create_task(client, token, task_type="SERVICE_CALL")["task_type"] == "SERVICE_CALL"


def test_engineer_cannot_create_task(client, seeded):
    token = login(client, "eng1", ENGINEER_PASSWORD)
    response = client.post(
        "/api/tasks",
        json={"task_type": "SERVICE_CALL", "scheduled_date": NEXT_TUESDAY},
        headers=auth_headers(token),
    )
    assert response.status_code == 403


def test_assignment_moves_task_to_assigned(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, token)

    response = client.post(
        f"/api/tasks/{task['id']}/assign",
        json={"engineer_id": seeded["engineer_one"].id},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ASSIGNED"
    assert response.json()["assigned_engineer"]["username"] == "eng1"


def test_engineer_only_sees_own_tasks(client, seeded):
    owner_token = login(client, "owner", PROPRIETOR_PASSWORD)
    mine = create_task(client, owner_token, customer_name="Mine")
    theirs = create_task(client, owner_token, customer_name="Theirs")
    client.post(
        f"/api/tasks/{mine['id']}/assign",
        json={"engineer_id": seeded["engineer_one"].id},
        headers=auth_headers(owner_token),
    )
    client.post(
        f"/api/tasks/{theirs['id']}/assign",
        json={"engineer_id": seeded["engineer_two"].id},
        headers=auth_headers(owner_token),
    )

    engineer_token = login(client, "eng1", ENGINEER_PASSWORD)
    listed = client.get("/api/tasks", headers=auth_headers(engineer_token)).json()
    assert [t["customer_name"] for t in listed] == ["Mine"]

    # Directly calling the endpoint for someone else's task is still refused.
    forbidden = client.get(f"/api/tasks/{theirs['id']}", headers=auth_headers(engineer_token))
    assert forbidden.status_code == 403


def test_full_workflow_to_completion(client, seeded):
    owner_token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, owner_token)
    task_id = task["id"]

    client.post(
        f"/api/tasks/{task_id}/assign",
        json={"engineer_id": seeded["engineer_one"].id},
        headers=auth_headers(owner_token),
    )

    engineer_token = login(client, "eng1", ENGINEER_PASSWORD)
    headers = auth_headers(engineer_token)

    # Engineer fills in the task information.
    updated = client.patch(
        f"/api/tasks/{task_id}",
        json={"model": "XR-200", "meter_reading": "14520"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["meter_reading"] == "14520"

    started = client.post(
        f"/api/tasks/{task_id}/status", json={"status": "IN_PROGRESS"}, headers=headers
    )
    assert started.json()["status"] == "IN_PROGRESS"

    completed = client.post(
        f"/api/tasks/{task_id}/status", json={"status": "COMPLETED"}, headers=headers
    )
    assert completed.json()["status"] == "COMPLETED"


def test_status_cannot_skip_steps(client, seeded):
    owner_token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, owner_token)
    response = client.post(
        f"/api/tasks/{task['id']}/status",
        json={"status": "COMPLETED"},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


def test_engineer_cannot_progress_a_task_assigned_to_someone_else(client, seeded):
    owner_token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, owner_token)
    client.post(
        f"/api/tasks/{task['id']}/assign",
        json={"engineer_id": seeded["engineer_two"].id},
        headers=auth_headers(owner_token),
    )

    other_token = login(client, "eng1", ENGINEER_PASSWORD)
    response = client.post(
        f"/api/tasks/{task['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=auth_headers(other_token),
    )
    assert response.status_code == 403


def test_engineer_cannot_change_scheduled_date(client, seeded):
    owner_token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, owner_token)
    client.post(
        f"/api/tasks/{task['id']}/assign",
        json={"engineer_id": seeded["engineer_one"].id},
        headers=auth_headers(owner_token),
    )

    engineer_token = login(client, "eng1", ENGINEER_PASSWORD)
    response = client.patch(
        f"/api/tasks/{task['id']}",
        json={"scheduled_date": date.today().isoformat()},
        headers=auth_headers(engineer_token),
    )
    assert response.status_code == 403


def test_completed_task_is_read_only(client, seeded):
    owner_token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, owner_token, assigned_engineer_id=seeded["engineer_one"].id)
    headers = auth_headers(owner_token)
    client.post(f"/api/tasks/{task['id']}/status", json={"status": "IN_PROGRESS"}, headers=headers)
    client.post(f"/api/tasks/{task['id']}/status", json={"status": "COMPLETED"}, headers=headers)

    response = client.patch(
        f"/api/tasks/{task['id']}", json={"model": "changed"}, headers=headers
    )
    assert response.status_code == 422


# --- "assign to myself" ---------------------------------------------------


def test_proprietor_can_assign_a_task_to_themselves(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, token)
    owner_id = seeded["proprietor"].id

    response = client.post(
        f"/api/tasks/{task['id']}/assign",
        json={"engineer_id": owner_id},
        headers=auth_headers(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assigned_engineer"]["id"] == owner_id
    assert body["status"] == "ASSIGNED"


def test_self_assigned_proprietor_can_run_the_task_to_completion(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, token, assigned_engineer_id=seeded["proprietor"].id)

    for target in ("IN_PROGRESS", "COMPLETED"):
        response = client.post(
            f"/api/tasks/{task['id']}/status",
            json={"status": target},
            headers=auth_headers(token),
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == target


def test_assignable_list_puts_the_proprietor_first(client, seeded):
    token = login(client, "owner", PROPRIETOR_PASSWORD)
    response = client.get("/api/users/assignable", headers=auth_headers(token))

    assert response.status_code == 200
    people = response.json()
    assert people[0]["id"] == seeded["proprietor"].id
    assert {p["id"] for p in people} == {
        seeded["proprietor"].id,
        seeded["engineer_one"].id,
        seeded["engineer_two"].id,
    }


def test_engineers_cannot_see_the_assignable_list(client, seeded):
    token = login(client, "eng1", ENGINEER_PASSWORD)
    response = client.get("/api/users/assignable", headers=auth_headers(token))
    assert response.status_code == 403


def test_a_task_cannot_be_assigned_to_another_proprietor(client, seeded, db):
    from app.domain.enums import UserRole
    from app.services.auth_service import AuthService

    other = AuthService(db).create_user(
        username="owner2", full_name="Second Owner",
        role=UserRole.PROPRIETOR, password=PROPRIETOR_PASSWORD,
    )
    db.commit()

    token = login(client, "owner", PROPRIETOR_PASSWORD)
    task = create_task(client, token)
    response = client.post(
        f"/api/tasks/{task['id']}/assign",
        json={"engineer_id": other.id},
        headers=auth_headers(token),
    )
    assert response.status_code == 422, response.text


# --- role-specific list scope --------------------------------------------


def test_engineers_are_never_offered_the_yet_to_assign_filter():
    from app.domain.enums import TaskStatus, UserRole
    from app.domain.task_workflow import visible_statuses

    engineer_view = visible_statuses(UserRole.SERVICE_ENGINEER)
    assert TaskStatus.YET_TO_ASSIGN not in engineer_view
    assert TaskStatus.ASSIGNED in engineer_view
    assert TaskStatus.IN_PROGRESS in engineer_view
    assert TaskStatus.COMPLETED in engineer_view
    assert visible_statuses(UserRole.PROPRIETOR) == list(TaskStatus)


def test_today_view_only_returns_tasks_scheduled_for_today(client, seeded, db):
    from app.services.task_service import TaskService

    token = login(client, "owner", PROPRIETOR_PASSWORD)
    create_task(client, token, scheduled_date=date.today().isoformat(),
                customer_name="Today Customer")
    create_task(client, token, customer_name="Next Week Customer")

    today = TaskService(db).list_today(seeded["proprietor"])
    assert [t.customer_name for t in today] == ["Today Customer"]
