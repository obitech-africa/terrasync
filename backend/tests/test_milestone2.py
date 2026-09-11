from datetime import datetime, timedelta, timezone

from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.models import ActivationCode, Site, User


def seed_m2_users():
    with SessionLocal() as db:
        tech = User(username="m2tech", full_name="M2 Technician", role="FIELD_TECHNICIAN", staff_no="M2-TECH", active=True)
        coord = User(username="m2coord", full_name="M2 Coordinator", role="COORDINATOR", password_hash=hash_secret("secret123"), active=True)
        sup = User(username="m2sup", full_name="M2 Supervisor", role="SUPERVISOR", password_hash=hash_secret("secret123"), active=True)
        site = Site(code="M2-SITE", name="Milestone 2 Site", latitude=0.31, longitude=32.58)
        db.add_all([tech, coord, sup, site]);db.flush()
        db.add(ActivationCode(user_id=tech.id, code_hash=hash_secret("654321"), expires_at=datetime.now(timezone.utc)+timedelta(hours=1)))
        db.commit()
        return tech.id, site.id


def login(client, username):
    r=client.post("/api/v1/auth/staff-login", json={"username":username,"password":"secret123"})
    assert r.status_code==200, r.text
    return {"Authorization":f"Bearer {r.json()['access_token']}"}


def activate(client):
    r=client.post("/api/v1/auth/activate-device", json={"username":"m2tech","code":"654321","device_key":"m2-device","device_name":"M2 Phone","platform":"Android"})
    assert r.status_code==200, r.text
    return {"Authorization":f"Bearer {r.json()['access_token']}"}


def evidence(work_order_no):
    return {
        "kind":"photo","source":"live_camera","name":"verified.jpg","evidence_id":"m2-evidence-001",
        "sha256":"b"*64,"mime_type":"image/jpeg","content_base64":"/9j/4AAQSkZJRg==",
        "captured_at":"2026-09-01T09:00:00Z","latitude":0.31,"longitude":32.58,"accuracy_m":3.2,
        "device_id":"m2-device","inspector_name":"M2 Technician","work_order_no":work_order_no,
    }


def test_assignment_asset_report_review_flow(client):
    tech_id, site_id = seed_m2_users()
    coord=login(client,"m2coord")
    sup=login(client,"m2sup")
    tech=activate(client)

    created=client.post("/api/v1/assignments", headers=coord, json={
        "work_order_no":"WO-M2-001","site_id":site_id,"report_type":"Telecom Tower Inspection",
        "priority":"High","technician_id":tech_id
    })
    assert created.status_code==201, created.text
    work=created.json()

    started=client.post(f"/api/v1/assignments/{work['id']}/start", headers=tech)
    assert started.status_code==200
    assert started.json()["status"]=="In Progress"

    asset=client.post("/api/v1/assets", headers=tech, json={
        "client_id":"asset-m2-001","work_order_id":work["id"],"site_id":site_id,"asset_type":"RRU",
        "manufacturer":"ZTE","model":"R8854","serial_number":"SN-M2","quantity":3,
        "height_or_elevation":"53 m","condition":"Good","source":"on_site","evidence":[evidence("WO-M2-001")]
    })
    assert asset.status_code==201, asset.text

    payload={
        "client_id":"report-m2-001","work_order_id":work["id"],"site_id":site_id,"inspector_name":"M2 Technician",
        "report_type":"Telecom Tower Inspection","summary":"Unsafe access and severe corrosion.",
        "answers":{"structural_condition":"Poor","electrical_condition":"Good","safety_condition":"Unsafe","earth_resistance_ohm":7.2},
        "evidence":[evidence("WO-M2-001")],"latitude":0.31,"longitude":32.58,"captured_at":"2026-09-01T09:00:00Z","submit":True
    }
    sync=client.post("/api/v1/sync/push",headers=tech,json={"mutations":[{"mutation_id":"m2-report-mutation","entity":"report","operation":"upsert","payload":payload}]})
    assert sync.status_code==200, sync.text
    assert sync.json()["results"][0]["status"]=="applied"

    queue=client.get("/api/v1/review-queue",headers=coord)
    assert queue.status_code==200
    assert len(queue.json())==1
    report=queue.json()[0]
    assert report["ai_status"]=="screened"

    approved=client.post(f"/api/v1/reports/{report['id']}/review",headers=coord,json={"decision":"approve","note":"Reviewed"})
    assert approved.status_code==200
    assert approved.json()["status"]=="Approved"

    sup_dash=client.get("/api/v1/dashboard/supervisor",headers=sup)
    assert sup_dash.status_code==200
    assert sup_dash.json()["completed"]==1


def test_technician_cannot_create_asset_for_other_assignment(client):
    tech_id, site_id = seed_m2_users()
    coord=login(client,"m2coord")
    tech=activate(client)
    other = User(username="othertech", full_name="Other Tech", role="FIELD_TECHNICIAN", active=True)
    with SessionLocal() as db:
        db.add(other);db.commit();other_id=other.id

    created=client.post("/api/v1/assignments",headers=coord,json={
        "work_order_no":"WO-M2-OTHER","site_id":site_id,"report_type":"Solar PV Site Inspection",
        "priority":"Medium","technician_id":other_id
    }).json()
    response=client.post("/api/v1/assets",headers=tech,json={
        "client_id":"asset-forbidden","work_order_id":created["id"],"site_id":site_id,"asset_type":"Inverter",
        "quantity":1,"condition":"Good","source":"on_site","evidence":[evidence("WO-M2-OTHER")]
    })
    assert response.status_code==403
