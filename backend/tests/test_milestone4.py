from app.db.session import SessionLocal
from app.services.configuration_seed import seed_configuration
from app.services.demo import seed_demo


def seed_m4():
    with SessionLocal() as db:
        seed_demo(db)
        seed_configuration(db)



def staff_headers(client):
    seed_m4()
    response = client.post(
        "/api/v1/auth/staff-login",
        json={"username": "coordinator", "password": "demo123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_seeded_m4_configuration(client):
    headers = staff_headers(client)
    assert client.get("/api/v1/configuration/clients", headers=headers).status_code == 200
    assert client.get("/api/v1/configuration/projects", headers=headers).status_code == 200
    templates = client.get("/api/v1/configuration/templates", headers=headers)
    assert templates.status_code == 200
    assert len(templates.json()) >= 10


def test_create_client_and_project(client):
    headers = staff_headers(client)
    response = client.post(
        "/api/v1/configuration/clients",
        headers=headers,
        json={"name": "Energy Client", "code": "ENERGY-1", "sector": "Energy", "branding": {}},
    )
    assert response.status_code == 201
    client_id = response.json()["id"]

    response = client.post(
        "/api/v1/configuration/projects",
        headers=headers,
        json={"client_id": client_id, "name": "Solar Rollout", "code": "SOLAR-1", "sector": "Energy", "settings": {}},
    )
    assert response.status_code == 201
    assert response.json()["client_id"] == client_id


def test_template_version_publish(client):
    headers = staff_headers(client)
    response = client.post(
        "/api/v1/configuration/templates",
        headers=headers,
        json={
            "name": "Custom Utility Template",
            "slug": "custom-utility-m4-test",
            "sector": "Utilities",
            "category": "inspection",
            "description": "Configurable template",
            "definition": {
                "id": "custom-utility-m4-test",
                "name": "Custom Utility Template",
                "sector": "Utilities",
                "category": "inspection",
                "version": 1,
                "description": "Configurable template",
                "asset_types": [],
                "sections": [],
            },
        },
    )
    assert response.status_code == 201
    template_id = response.json()["id"]

    response = client.post(
        f"/api/v1/configuration/templates/{template_id}/versions",
        headers=headers,
        json={
            "definition": {
                "id": "custom-utility-m4-test",
                "name": "Custom Utility Template",
                "sector": "Utilities",
                "category": "inspection",
                "version": 2,
                "description": "Updated",
                "asset_types": [],
                "sections": [],
            },
            "changelog": "Version 2",
        },
    )
    assert response.status_code == 201
    version_id = response.json()["id"]

    response = client.post(
        f"/api/v1/configuration/templates/{template_id}/versions/{version_id}/publish",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["version"] == 2


def test_asset_ai_and_report_config(client):
    headers = staff_headers(client)
    client_row = client.get("/api/v1/configuration/clients", headers=headers).json()[0]
    project = client.get("/api/v1/configuration/projects", headers=headers).json()[0]

    response = client.post(
        "/api/v1/configuration/asset-schemas",
        headers=headers,
        json={
            "client_id": client_row["id"],
            "project_id": project["id"],
            "name": "Generator Schema",
            "asset_type": "Generator",
            "fields": [{"key": "rated_power_kva", "label": "Rated power", "type": "number"}],
            "evidence_rules": {"live_camera_required": True},
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/configuration/ai-rules",
        headers=headers,
        json={
            "client_id": client_row["id"],
            "project_id": project["id"],
            "name": "Generator AI",
            "rules": [{"type": "numeric_threshold", "field": "frequency_hz", "operator": "<", "value": 49}],
            "thresholds": {"high_risk_score": 70},
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/configuration/report-layouts",
        headers=headers,
        json={
            "client_id": client_row["id"],
            "project_id": project["id"],
            "name": "Compact Report",
            "layout": {"target_pdf_mb": 5, "photo_grid_columns": 2},
            "compression_profile": "compact",
        },
    )
    assert response.status_code == 201


def test_field_template_api_uses_database(client):
    seed_m4()
    response = client.get("/api/v1/inspection-templates")
    assert response.status_code == 200
    assert len(response.json()) >= 10
    assert all("database_id" in item for item in response.json())
