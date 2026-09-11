import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.data.templates.index import get_default_templates
from app.db.session import get_db
from app.models.inspection_template import InspectionTemplate
from app.schemas.inspection_template import (
    InspectionTemplateCreate,
    InspectionTemplateRead,
    TemplateSelectRequest,
)


router = APIRouter()


def serialize_template(template: InspectionTemplate) -> dict:
    return {
        "id": template.id,
        "template_id": template.template_id,
        "name": template.name,
        "industry": template.industry,
        "company_type": template.company_type,
        "asset_type": template.asset_type,
        "inspection_type": template.inspection_type,
        "category": template.category,
        "version": template.version,
        "status": template.status,
        "template_info": json.loads(template.template_info),
        "sections": json.loads(template.sections),
    }


@router.get("/", response_model=list[InspectionTemplateRead])
def list_templates(db: Session = Depends(get_db)):
    templates = (
        db.query(InspectionTemplate)
        .order_by(InspectionTemplate.id.desc())
        .all()
    )

    return [serialize_template(template) for template in templates]


@router.post(
    "/",
    response_model=InspectionTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_template(
    template_in: InspectionTemplateCreate,
    db: Session = Depends(get_db),
):
    existing_template = (
        db.query(InspectionTemplate)
        .filter(InspectionTemplate.template_id == template_in.template_id)
        .first()
    )

    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template ID already exists.",
        )

    template = InspectionTemplate(
        template_id=template_in.template_id,
        name=template_in.name,
        industry=template_in.industry,
        company_type=template_in.company_type,
        asset_type=template_in.asset_type,
        inspection_type=template_in.inspection_type,
        category=template_in.category,
        version=template_in.version,
        status=template_in.status,
        template_info=json.dumps(template_in.template_info),
        sections=json.dumps(template_in.sections),
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return serialize_template(template)


@router.post("/seed-defaults", response_model=dict)
def seed_default_templates(db: Session = Depends(get_db)):
    default_templates = get_default_templates()

    created_templates = []
    skipped_templates = []

    for template_data in default_templates:
        existing_template = (
            db.query(InspectionTemplate)
            .filter(InspectionTemplate.template_id == template_data["template_id"])
            .first()
        )

        if existing_template:
            skipped_templates.append(template_data["template_id"])
            continue

        template = InspectionTemplate(
            template_id=template_data["template_id"],
            name=template_data["name"],
            industry=template_data["industry"],
            company_type=template_data["company_type"],
            asset_type=template_data["asset_type"],
            inspection_type=template_data["inspection_type"],
            category=template_data["category"],
            version=template_data["version"],
            status=template_data["status"],
            template_info=json.dumps(template_data["template_info"]),
            sections=json.dumps(template_data["sections"]),
        )

        db.add(template)
        created_templates.append(template_data["template_id"])

    db.commit()

    return {
        "message": "Default inspection templates seeded successfully.",
        "total_default_templates": len(default_templates),
        "created_count": len(created_templates),
        "skipped_count": len(skipped_templates),
        "created_templates": created_templates,
        "skipped_templates": skipped_templates,
    }


@router.post("/select", response_model=InspectionTemplateRead)
def select_template(
    selection: TemplateSelectRequest,
    db: Session = Depends(get_db),
):
    template = (
        db.query(InspectionTemplate)
        .filter(InspectionTemplate.industry == selection.industry)
        .filter(InspectionTemplate.company_type == selection.company_type)
        .filter(InspectionTemplate.asset_type == selection.asset_type)
        .filter(InspectionTemplate.inspection_type == selection.inspection_type)
        .filter(InspectionTemplate.status == "Active")
        .first()
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active inspection template found for the selected industry, company type, asset type, and inspection type.",
        )

    return serialize_template(template)


@router.get("/defaults", response_model=dict)
def preview_default_templates():
    templates = get_default_templates()

    return {
        "count": len(templates),
        "templates": templates,
    }


@router.get("/defaults/{template_id}", response_model=dict)
def preview_default_template_by_id(template_id: str):
    templates = get_default_templates()

    for template in templates:
        if template["template_id"] == template_id:
            return template

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Default template not found.",
    )