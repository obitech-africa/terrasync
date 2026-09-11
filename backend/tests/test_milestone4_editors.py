
from app.db.session import SessionLocal
from app.services.configuration_seed import seed_configuration
from app.services.demo import seed_demo


def login(client):
    with SessionLocal() as db:
        seed_demo(db)
        seed_configuration(db)

    response = client.post(
        "/api/v1/auth/staff-login",
        json={"username": "coordinator", "password": "demo123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_template_editor_update_delete(client):
    headers = login(client)
    create = client.post(
        "/api/v1/configuration/templates",
        headers=headers,
        json={
            "name": "Editor Test",
            "slug": "editor-test",
            "sector": "Utilities",
            "category": "inspection",
            "description": "draft",
            "definition": {
                "id": "editor-test",
                "name": "Editor Test",
                "sector": "Utilities",
                "category": "inspection",
                "version": 1,
                "description": "draft",
                "asset_types": [],
                "sections": [],
            },
        },
    )
    assert create.status_code == 201
    template_id = create.json()["id"]

    update = client.put(
        f"/api/v1/configuration/templates/{template_id}",
        headers=headers,
        json={
            "name": "Editor Test Updated",
            "slug": "editor-test",
            "sector": "Utilities",
            "category": "survey",
            "description": "updated",
            "definition": {
                "id": "editor-test",
                "name": "Editor Test Updated",
                "sector": "Utilities",
                "category": "survey",
                "version": 1,
                "description": "updated",
                "asset_types": [],
                "sections": [{"id": "site", "title": "Site", "evidence_min": 1, "fields": []}],
            },
        },
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Editor Test Updated"

    delete = client.delete(
        f"/api/v1/configuration/templates/{template_id}",
        headers=headers,
    )
    assert delete.status_code == 204


def test_asset_ai_layout_editor_updates(client):
    headers = login(client)
    clients = client.get("/api/v1/configuration/clients", headers=headers).json()
    projects = client.get("/api/v1/configuration/projects", headers=headers).json()

    asset = client.post(
        "/api/v1/configuration/asset-schemas",
        headers=headers,
        json={
            "client_id": clients[0]["id"],
            "project_id": projects[0]["id"],
            "name": "Editable Pump",
            "asset_type": "Pump",
            "fields": [],
            "evidence_rules": {"live_camera_required": True},
        },
    ).json()

    updated_asset = client.put(
        f"/api/v1/configuration/asset-schemas/{asset['id']}",
        headers=headers,
        json={
            "client_id": clients[0]["id"],
            "project_id": projects[0]["id"],
            "name": "Editable Pump Updated",
            "asset_type": "Pump",
            "fields": [{"key": "flow", "label": "Flow", "type": "number"}],
            "evidence_rules": {"live_camera_required": True},
        },
    )
    assert updated_asset.status_code == 200
    assert len(updated_asset.json()["fields"]) == 1

    rules = client.post(
        "/api/v1/configuration/ai-rules",
        headers=headers,
        json={
            "name": "Editable AI",
            "rules": [],
            "thresholds": {},
        },
    ).json()
    updated_rules = client.put(
        f"/api/v1/configuration/ai-rules/{rules['id']}",
        headers=headers,
        json={
            "name": "Editable AI Updated",
            "rules": [{"type": "required_evidence", "severity": "high"}],
            "thresholds": {"high_risk_score": 70},
        },
    )
    assert updated_rules.status_code == 200

    layout = client.post(
        "/api/v1/configuration/report-layouts",
        headers=headers,
        json={
            "name": "Editable Layout",
            "layout": {"target_pdf_mb": 5},
            "compression_profile": "compact",
        },
    ).json()
    updated_layout = client.put(
        f"/api/v1/configuration/report-layouts/{layout['id']}",
        headers=headers,
        json={
            "name": "Editable Layout Updated",
            "layout": {"target_pdf_mb": 10, "photo_grid_columns": 3},
            "compression_profile": "standard",
        },
    )
    assert updated_layout.status_code == 200
    assert updated_layout.json()["compression_profile"] == "standard"
