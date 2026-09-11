from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIFinding, ChangeEvent, InspectionReport, Site, WorkOrder
from app.schemas.domain import FindingOut, ReportCreate, ReportOut, ReportUpdate
from app.services.ai_screening import persist_screening
from app.services.reports import build_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def next_report_no(db: Session) -> str:
    count = len(list(db.scalars(select(InspectionReport.id))))
    return f"RPT-{datetime.now(timezone.utc).year}-{count + 1:05d}"


def validate_links(db: Session, work_order_id: str, site_id: str) -> None:
    work_order = db.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    if not db.get(Site, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    if work_order.site_id != site_id:
        raise HTTPException(status_code=422, detail="Work order does not belong to selected site")


def create_or_get_report(db: Session, payload: ReportCreate) -> InspectionReport:
    existing = db.scalar(select(InspectionReport).where(InspectionReport.client_id == payload.client_id))
    if existing:
        return existing

    validate_links(db, payload.work_order_id, payload.site_id)
    data = payload.model_dump(exclude={"submit"})
    data["evidence"] = [item.model_dump(mode="json") for item in payload.evidence]
    report = InspectionReport(
        **data,
        report_no=next_report_no(db),
        status="Submitted" if payload.submit else "Draft",
        submitted_at=datetime.now(timezone.utc) if payload.submit else None,
    )
    db.add(report)
    db.flush()
    db.add(
        ChangeEvent(
            entity_type="report",
            entity_id=report.id,
            operation="upsert",
            payload={"client_id": report.client_id, "report_no": report.report_no, "revision": report.revision},
        )
    )
    db.commit()
    db.refresh(report)
    if payload.submit:
        persist_screening(db, report)
        db.refresh(report)
    return report


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db)) -> list[InspectionReport]:
    return list(db.scalars(select(InspectionReport).order_by(InspectionReport.updated_at.desc())))


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)) -> InspectionReport:
    return create_or_get_report(db, payload)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)) -> InspectionReport:
    report = db.get(InspectionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}", response_model=ReportOut)
def update_report(report_id: str, payload: ReportUpdate, db: Session = Depends(get_db)) -> InspectionReport:
    report = db.get(InspectionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if payload.revision != report.revision:
        raise HTTPException(status_code=409, detail={"message": "Revision conflict", "server_revision": report.revision})

    updates = payload.model_dump(exclude_none=True, exclude={"revision"})
    if "evidence" in updates:
        updates["evidence"] = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in payload.evidence or []]
    for key, value in updates.items():
        setattr(report, key, value)
    report.revision += 1
    if report.status == "Submitted" and report.submitted_at is None:
        report.submitted_at = datetime.now(timezone.utc)

    db.add(
        ChangeEvent(
            entity_type="report",
            entity_id=report.id,
            operation="upsert",
            payload={"client_id": report.client_id, "report_no": report.report_no, "revision": report.revision},
        )
    )
    db.commit()
    db.refresh(report)
    if report.status == "Submitted":
        persist_screening(db, report)
        db.refresh(report)
    return report


@router.post("/{report_id}/screen", response_model=list[FindingOut])
def screen(report_id: str, db: Session = Depends(get_db)) -> list[AIFinding]:
    report = db.get(InspectionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return persist_screening(db, report)


@router.get("/{report_id}/findings", response_model=list[FindingOut])
def findings(report_id: str, db: Session = Depends(get_db)) -> list[AIFinding]:
    if not db.get(InspectionReport, report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return list(
        db.scalars(
            select(AIFinding)
            .where(AIFinding.report_id == report_id)
            .order_by(AIFinding.created_at)
        )
    )


@router.get("/{report_id}/pdf")
def report_pdf(report_id: str, db: Session = Depends(get_db)) -> Response:
    report = db.get(InspectionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.ai_status != "screened":
        persist_screening(db, report)
        db.refresh(report)
    pdf = build_report_pdf(db, report)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report.report_no}.pdf"'},
    )
