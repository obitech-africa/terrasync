def test_template_catalog_contains_inspections_and_surveys(client):
    response = client.get("/api/v1/inspection-templates")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 9
    assert any(item["category"] == "inspection" for item in templates)
    assert any(item["category"] == "survey" for item in templates)
    assert any(item["sector"] == "Telecommunications" for item in templates)
    assert any(item["sector"] == "Energy" for item in templates)
    assert any(item["sector"] == "Utilities" for item in templates)


def test_atc_style_tower_template_has_staged_sections(client):
    response = client.get("/api/v1/inspection-templates/telecom-tower-maintenance-v1")
    assert response.status_code == 200
    template = response.json()
    section_ids = {item["id"] for item in template["sections"]}
    assert "preclimb-surrounding" in section_ids
    assert "climb-up" in section_ids
    assert "tower-top" in section_ids
    assert "equipment-inventory" in section_ids
    assert "post-climb" in section_ids
    assert template["source_basis"] == "ATC-style tower maintenance reference"


def test_template_filter_supports_sector_and_category(client):
    response = client.get(
        "/api/v1/inspection-templates",
        params={"sector": "Energy", "category": "survey"},
    )
    assert response.status_code == 200
    templates = response.json()
    assert templates
    assert all(item["sector"] == "Energy" for item in templates)
    assert all(item["category"] == "survey" for item in templates)


def test_template_validator_reports_missing_required_data(client):
    response = client.post(
        "/api/v1/inspection-templates/solar-site-survey-v1/validate",
        json={"answers": {}, "evidence": []},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is False
    assert result["missing_fields"]
    assert result["missing_evidence"]


def test_template_validator_accepts_complete_compact_generator_payload(client):
    template = client.get(
        "/api/v1/inspection-templates/generator-backup-power-v1"
    ).json()

    answers = {}
    evidence = []
    for section in template["sections"]:
        for item in section["fields"]:
            if item["required"]:
                if item["type"] == "number":
                    answers[item["key"]] = 1
                elif item["type"] == "select":
                    answers[item["key"]] = item["options"][0]
                else:
                    answers[item["key"]] = "Checked"
        for index in range(section.get("evidence_min", 0)):
            evidence.append(
                {
                    "section_id": section["id"],
                    "evidence_id": f"{section['id']}-{index}",
                }
            )

    response = client.post(
        "/api/v1/inspection-templates/generator-backup-power-v1/validate",
        json={"answers": answers, "evidence": evidence},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True
