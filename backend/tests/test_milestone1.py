from datetime import datetime, timedelta, timezone

from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.models import ActivationCode, Site, User


def seed_auth():
    with SessionLocal() as db:
        tech = User(
            username="tech1",
            full_name="Test Technician",
            role="FIELD_TECHNICIAN",
            staff_no="TECH-1",
            active=True,
        )
        coordinator = User(
            username="coord1",
            full_name="Test Coordinator",
            role="COORDINATOR",
            password_hash=hash_secret("secret123"),
            active=True,
        )
        supervisor = User(
            username="super1",
            full_name="Test Supervisor",
            role="SUPERVISOR",
            password_hash=hash_secret("secret123"),
            active=True,
        )
        site = Site(code="AUTH-SITE", name="Authentication Site")
        db.add_all([tech, coordinator, supervisor, site])
        db.flush()
        db.add(
            ActivationCode(
                user_id=tech.id,
                code_hash=hash_secret("123456"),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
        )
        db.commit()
        return tech.id, coordinator.id, supervisor.id, site.id


def activate(client):
    response = client.post(
        "/api/v1/auth/activate-device",
        json={
            "username": "tech1",
            "code": "123456",
            "device_key": "device-key-123456",
            "device_name": "Test Phone",
            "platform": "Android",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def login(client, username):
    response = client.post(
        "/api/v1/auth/staff-login",
        json={"username": username, "password": "secret123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_one_time_activation_and_persistent_device_session(client):
    seed_auth()
    data = activate(client)
    token = data["access_token"]
    assert data["user"]["role"] == "FIELD_TECHNICIAN"

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "tech1"

    reused = client.post(
        "/api/v1/auth/activate-device",
        json={
            "username": "tech1",
            "code": "123456",
            "device_key": "another-device-key",
            "device_name": "Second Phone",
            "platform": "Android",
        },
    )
    assert reused.status_code == 401


def test_role_protection(client):
    seed_auth()
    tech_token = activate(client)["access_token"]
    response = client.get(
        "/api/v1/dashboard/supervisor",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert response.status_code == 403

    supervisor_token = login(client, "super1")
    response = client.get(
        "/api/v1/dashboard/supervisor",
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert response.status_code == 200


def test_coordinator_assignment_reaches_technician(client):
    tech_id, _, _, site_id = seed_auth()
    tech_token = activate(client)["access_token"]
    coordinator_token = login(client, "coord1")

    created = client.post(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {coordinator_token}"},
        json={
            "work_order_no": "WO-AUTH-001",
            "site_id": site_id,
            "report_type": "Tower Maintenance Inspection",
            "priority": "High",
            "technician_id": tech_id,
        },
    )
    assert created.status_code == 201, created.text

    technician_dashboard = client.get(
        "/api/v1/dashboard/technician",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert technician_dashboard.status_code == 200
    body = technician_dashboard.json()
    assert body["assigned"] == 1
    assert body["assignments"][0]["work_order_no"] == "WO-AUTH-001"


def test_coordinator_and_supervisor_dashboards(client):
    seed_auth()
    coordinator = login(client, "coord1")
    supervisor = login(client, "super1")

    coord = client.get(
        "/api/v1/dashboard/coordinator",
        headers={"Authorization": f"Bearer {coordinator}"},
    )
    sup = client.get(
        "/api/v1/dashboard/supervisor",
        headers={"Authorization": f"Bearer {supervisor}"},
    )
    assert coord.status_code == 200
    assert sup.status_code == 200
    assert "awaiting_review" in coord.json()
    assert "overdue" in sup.json()
