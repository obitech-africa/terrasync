from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.configuration import (
    AIRuleSet,
    AssetSchema,
    Client,
    Project,
    ReportLayout,
    TemplateDefinition,
    TemplateVersion,
)
from app.schemas.configuration import (
    AIRuleSetCreate,
    AssetSchemaCreate,
    ClientCreate,
    ProjectCreate,
    ReportLayoutCreate,
    TemplateCreate,
    TemplateVersionCreate,
)

router = APIRouter(prefix="/configuration", tags=["configuration"])
manage = require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")


def serialize(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


@router.get("/clients")
def list_clients(db: Session = Depends(get_db), _=Depends(manage)):
    return [serialize(x) for x in db.query(Client).order_by(Client.name).all()]


@router.post("/clients", status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), _=Depends(manage)):
    if db.query(Client).filter(Client.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Client code already exists")
    row = Client(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get("/projects")
def list_projects(db: Session = Depends(get_db), _=Depends(manage)):
    return [serialize(x) for x in db.query(Project).order_by(Project.name).all()]


@router.post("/projects", status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), _=Depends(manage)):
    if not db.get(Client, payload.client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    row = Project(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get("/templates")
def list_templates(db: Session = Depends(get_db), _=Depends(manage)):
    result = []
    for row in db.query(TemplateDefinition).order_by(TemplateDefinition.sector, TemplateDefinition.name):
        data = serialize(row)
        active = db.get(TemplateVersion, row.active_version_id) if row.active_version_id else None
        data["active_version"] = active.version if active else None
        data["status"] = active.status if active else None
        result.append(data)
    return result


@router.post("/templates", status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db), _=Depends(manage)):
    if db.query(TemplateDefinition).filter(TemplateDefinition.slug == payload.slug).first():
        raise HTTPException(status_code=409, detail="Template slug already exists")
    row = TemplateDefinition(
        client_id=payload.client_id,
        name=payload.name,
        slug=payload.slug,
        sector=payload.sector,
        category=payload.category,
        description=payload.description,
    )
    db.add(row)
    db.flush()
    version = TemplateVersion(
        template_id=row.id,
        version=1,
        status="draft",
        definition=payload.definition,
    )
    db.add(version)
    db.flush()
    row.active_version_id = version.id
    db.commit()
    return {"id": row.id, "version_id": version.id, "status": version.status}



@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(TemplateDefinition, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    active = db.get(TemplateVersion, row.active_version_id) if row.active_version_id else None
    result = serialize(row)
    result["active_version"] = serialize(active) if active else None
    result["versions"] = [
        serialize(version)
        for version in db.query(TemplateVersion)
        .filter(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.version.desc())
        .all()
    ]
    return result


@router.post("/templates/{template_id}/versions", status_code=201)
def add_version(template_id: str, payload: TemplateVersionCreate, db: Session = Depends(get_db), _=Depends(manage)):
    template = db.get(TemplateDefinition, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    latest = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).order_by(TemplateVersion.version.desc()).first()
    row = TemplateVersion(
        template_id=template_id,
        version=(latest.version + 1) if latest else 1,
        status="draft",
        definition=payload.definition,
        changelog=payload.changelog,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.post("/templates/{template_id}/versions/{version_id}/publish")
def publish_version(template_id: str, version_id: str, db: Session = Depends(get_db), _=Depends(manage)):
    template = db.get(TemplateDefinition, template_id)
    version = db.get(TemplateVersion, version_id)
    if not template or not version or version.template_id != template_id:
        raise HTTPException(status_code=404, detail="Template version not found")
    version.status = "published"
    version.published_at = datetime.now(timezone.utc)
    template.active_version_id = version.id
    db.commit()
    return {"status": "published", "version": version.version}


@router.get("/asset-schemas")
def list_asset_schemas(db: Session = Depends(get_db), _=Depends(manage)):
    return [serialize(x) for x in db.query(AssetSchema).order_by(AssetSchema.asset_type).all()]


@router.post("/asset-schemas", status_code=201)
def create_asset_schema(payload: AssetSchemaCreate, db: Session = Depends(get_db), _=Depends(manage)):
    row = AssetSchema(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get("/ai-rules")
def list_ai_rules(db: Session = Depends(get_db), _=Depends(manage)):
    return [serialize(x) for x in db.query(AIRuleSet).order_by(AIRuleSet.name).all()]


@router.post("/ai-rules", status_code=201)
def create_ai_rules(payload: AIRuleSetCreate, db: Session = Depends(get_db), _=Depends(manage)):
    row = AIRuleSet(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.get("/report-layouts")
def list_report_layouts(db: Session = Depends(get_db), _=Depends(manage)):
    return [serialize(x) for x in db.query(ReportLayout).order_by(ReportLayout.name).all()]


@router.post("/report-layouts", status_code=201)
def create_report_layout(payload: ReportLayoutCreate, db: Session = Depends(get_db), _=Depends(manage)):
    row = ReportLayout(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.put("/templates/{template_id}")
def update_template(
    template_id: str,
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(TemplateDefinition, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    row.client_id = payload.client_id
    row.name = payload.name
    row.slug = payload.slug
    row.sector = payload.sector
    row.category = payload.category
    row.description = payload.description

    active = db.get(TemplateVersion, row.active_version_id) if row.active_version_id else None
    if active and active.status == "draft":
        active.definition = payload.definition
    else:
        latest = (
            db.query(TemplateVersion)
            .filter(TemplateVersion.template_id == template_id)
            .order_by(TemplateVersion.version.desc())
            .first()
        )
        version = TemplateVersion(
            template_id=template_id,
            version=(latest.version + 1) if latest else 1,
            status="draft",
            definition=payload.definition,
            changelog="Created by template editor.",
        )
        db.add(version)
        db.flush()
        row.active_version_id = version.id

    db.commit()
    return get_template(template_id, db)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(TemplateDefinition, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    versions = db.query(TemplateVersion).filter(
        TemplateVersion.template_id == template_id
    ).all()
    for version in versions:
        db.delete(version)
    db.delete(row)
    db.commit()
    return None


@router.put("/asset-schemas/{schema_id}")
def update_asset_schema(
    schema_id: str,
    payload: AssetSchemaCreate,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(AssetSchema, schema_id)
    if not row:
        raise HTTPException(status_code=404, detail="Asset schema not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.delete("/asset-schemas/{schema_id}", status_code=204)
def delete_asset_schema(
    schema_id: str,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(AssetSchema, schema_id)
    if not row:
        raise HTTPException(status_code=404, detail="Asset schema not found")
    db.delete(row)
    db.commit()
    return None


@router.put("/ai-rules/{rule_id}")
def update_ai_rules(
    rule_id: str,
    payload: AIRuleSetCreate,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(AIRuleSet, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="AI rule set not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.delete("/ai-rules/{rule_id}", status_code=204)
def delete_ai_rules(
    rule_id: str,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(AIRuleSet, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="AI rule set not found")
    db.delete(row)
    db.commit()
    return None


@router.put("/report-layouts/{layout_id}")
def update_report_layout(
    layout_id: str,
    payload: ReportLayoutCreate,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(ReportLayout, layout_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report layout not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return serialize(row)


@router.delete("/report-layouts/{layout_id}", status_code=204)
def delete_report_layout(
    layout_id: str,
    db: Session = Depends(get_db),
    _=Depends(manage),
):
    row = db.get(ReportLayout, layout_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report layout not found")
    db.delete(row)
    db.commit()
    return None
