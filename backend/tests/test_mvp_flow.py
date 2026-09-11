from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.models import User



def seed_sync_coordinator(client):
    with SessionLocal() as db:
        user = User(
            username="sync-coordinator",
            full_name="Sync Coordinator",
            role="COORDINATOR",
            password_hash=hash_secret("sync-secret"),
            active=True,
        )
        db.add(user)
        db.commit()
    response = client.post(
        "/api/v1/auth/staff-login",
        json={"username": "sync-coordinator", "password": "sync-secret"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def seed_site_and_work_order(client):
    site = client.post(
        "/api/v1/sites",
        json={"code": "TEST-001", "name": "Test Site", "latitude": 0.3, "longitude": 32.5},
    ).json()
    work_order = client.post(
        "/api/v1/work-orders",
        json={
            "work_order_no": "WO-TEST-001",
            "site_id": site["id"],
            "report_type": "Telecom Tower Inspection",
            "priority": "High",
        },
    ).json()
    return site, work_order


def report_payload(site, work_order, client_id="offline-001"):
    return {
        "client_id": client_id,
        "work_order_id": work_order["id"],
        "site_id": site["id"],
        "inspector_name": "Field Tester",
        "report_type": "Telecom Tower Inspection",
        "summary": "Severe corrosion and unsafe access area.",
        "answers": {
            "structural_condition": "Poor",
            "electrical_condition": "Good",
            "safety_condition": "Unsafe",
            "tower_tilt_deg": 2.4,
            "earth_resistance_ohm": 7.0,
            "battery_voltage_v": 52,
            "temperature_c": 35,
        },
        "evidence": [{
            "kind": "photo",
            "source": "live_camera",
            "name": "base.jpg",
            "evidence_id": "evidence-test-001",
            "sha256": "a" * 64,
            "mime_type": "image/jpeg",
            "content_base64": "/9j/4AAQSkZJRg==",
            "captured_at": "2026-09-01T08:00:00Z",
            "latitude": 0.3,
            "longitude": 32.5,
            "accuracy_m": 4.5,
            "device_id": "device-test-001",
            "inspector_name": "Field Tester",
            "work_order_no": "WO-TEST-001"
        }],
        "latitude": 0.3,
        "longitude": 32.5,
        "captured_at": "2026-09-01T08:00:00Z",
        "submit": True,
    }


def test_end_to_end_report_ai_and_pdf(client):
    site, work_order = seed_site_and_work_order(client)
    created = client.post("/api/v1/reports", json=report_payload(site, work_order))
    assert created.status_code == 201
    report = created.json()
    assert report["ai_status"] == "screened"
    assert report["ai_risk_score"] >= 45

    findings = client.get(f"/api/v1/reports/{report['id']}/findings")
    assert findings.status_code == 200
    assert any(item["severity"] == "Critical" for item in findings.json())

    pdf = client.get(f"/api/v1/reports/{report['id']}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_offline_sync_is_idempotent(client):
    site, work_order = seed_site_and_work_order(client)
    mutation = {
        "mutation_id": "m-1",
        "entity": "report",
        "operation": "upsert",
        "payload": report_payload(site, work_order, client_id="offline-idempotent"),
    }
    headers = seed_sync_coordinator(client)
    first = client.post("/api/v1/sync/push", json={"mutations": [mutation]}, headers=headers)
    assert first.status_code == 200
    assert first.json()["results"][0]["status"] == "applied"

    second = client.post("/api/v1/sync/push", json={"mutations": [mutation]}, headers=headers)
    assert second.status_code == 200
    assert second.json()["results"][0]["status"] == "duplicate"

    reports = client.get("/api/v1/reports").json()
    assert len(reports) == 1


def test_revision_conflict(client):
    site, work_order = seed_site_and_work_order(client)
    report = client.post("/api/v1/reports", json=report_payload(site, work_order, "revision-case")).json()
    update = client.patch(
        f"/api/v1/reports/{report['id']}",
        json={"revision": report["revision"], "summary": "Updated summary"},
    )
    assert update.status_code == 200

    conflict = client.patch(
        f"/api/v1/reports/{report['id']}",
        json={"revision": report["revision"], "summary": "Stale edit"},
    )
    assert conflict.status_code == 409


def test_submitted_report_rejects_missing_camera_evidence(client):
    site, work_order = seed_site_and_work_order(client)
    payload = report_payload(site, work_order, client_id="missing-camera")
    payload["evidence"] = []
    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 422


def test_submitted_report_rejects_location_mismatch(client):
    site, work_order = seed_site_and_work_order(client)
    payload = report_payload(site, work_order, client_id="location-mismatch")
    payload["latitude"] = 0.4
    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 422
