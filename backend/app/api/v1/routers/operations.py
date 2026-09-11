from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models import Defect, Device, InspectionReport, Site, User, WorkOrder
from app.schemas.auth import UserOut
from app.schemas.domain import ReportOut, ReviewDecision, WorkOrderOut

router = APIRouter(tags=["operations"])


class AssignmentCreate(BaseModel):
    work_order_no: str
    site_id: str
    report_type: str
    priority: str = "Medium"
    technician_id: str
    due_at: datetime | None = None


@router.get("/users/technicians", response_model=list[UserOut])
def technicians(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")),
) -> list[User]:
    return list(
        db.scalars(
            select(User).where(
                User.role == "FIELD_TECHNICIAN",
                User.active.is_(True),
            )
        )
    )


@router.get("/assignments", response_model=list[WorkOrderOut])
def assignments(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[WorkOrder]:
    stmt = select(WorkOrder).order_by(WorkOrder.created_at.desc())
    if user.role == "FIELD_TECHNICIAN":
        stmt = stmt.where(WorkOrder.assigned_user_id == user.id)
    elif user.role not in {"COORDINATOR", "SUPERVISOR", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return list(db.scalars(stmt))


@router.post("/assignments", response_model=WorkOrderOut, status_code=201)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")),
) -> WorkOrder:
    site = db.get(Site, payload.site_id)
    technician = db.get(User, payload.technician_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if not technician or technician.role != "FIELD_TECHNICIAN":
        raise HTTPException(status_code=404, detail="Technician not found")
    if db.scalar(select(WorkOrder).where(WorkOrder.work_order_no == payload.work_order_no)):
        raise HTTPException(status_code=409, detail="Work order number already exists")

    work_order = WorkOrder(
        work_order_no=payload.work_order_no,
        site_id=payload.site_id,
        report_type=payload.report_type,
        priority=payload.priority,
        status="Assigned",
        assigned_to=technician.full_name,
        assigned_user_id=technician.id,
        due_at=payload.due_at,
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


@router.get("/dashboard/technician")
def technician_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("FIELD_TECHNICIAN")),
) -> dict:
    work = list(
        db.scalars(
            select(WorkOrder)
            .where(WorkOrder.assigned_user_id == user.id)
            .order_by(WorkOrder.created_at.desc())
        )
    )
    return {
        "assigned": sum(item.status == "Assigned" for item in work),
        "in_progress": sum(item.status == "In Progress" for item in work),
        "completed": sum(item.status in {"Completed", "Submitted", "Closed"} for item in work),
        "assignments": [
            {
                "id": item.id,
                "work_order_no": item.work_order_no,
                "site_id": item.site_id,
                "report_type": item.report_type,
                "priority": item.priority,
                "status": item.status,
                "due_at": item.due_at,
                "site_name": (db.get(Site, item.site_id).name if db.get(Site, item.site_id) else item.site_id),
                "site_code": (db.get(Site, item.site_id).code if db.get(Site, item.site_id) else item.site_id),
            }
            for item in work
        ],
    }


@router.get("/dashboard/coordinator")
def coordinator_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")),
) -> dict:
    work = list(db.scalars(select(WorkOrder)))
    reports = list(
        db.scalars(
            select(InspectionReport).order_by(InspectionReport.created_at.desc())
        )
    )
    devices = list(db.scalars(select(Device)))
    technicians = list(
        db.scalars(select(User).where(User.role == "FIELD_TECHNICIAN"))
    )
    return {
        "assigned": sum(item.status == "Assigned" for item in work),
        "in_field": sum(item.status == "In Progress" for item in work),
        "awaiting_review": sum(
            item.status in {"Submitted", "Awaiting Review"} for item in reports
        ),
        "critical": sum((item.ai_risk_score or 0) >= 70 for item in reports),
        "active_technicians": sum(item.active for item in technicians),
        "registered_devices": sum(
            item.active and item.revoked_at is None for item in devices
        ),
        "recent_reports": [
            {
                "id": item.id,
                "report_no": item.report_no,
                "status": item.status,
                "risk": item.ai_risk_score,
                "summary": item.ai_summary,
            }
            for item in reports[:10]
        ],
    }


@router.get("/dashboard/supervisor")
def supervisor_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
) -> dict:
    work = list(db.scalars(select(WorkOrder)))
    reports = list(db.scalars(select(InspectionReport)))
    defects = list(db.scalars(select(Defect)))
    users = list(db.scalars(select(User)))
    now = datetime.now(timezone.utc)

    overdue = 0
    for item in work:
        if not item.due_at:
            continue
        due_at = item.due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        if due_at < now and item.status not in {"Completed", "Submitted", "Closed"}:
            overdue += 1

    return {
        "total_assignments": len(work),
        "completed": sum(
            item.status in {"Completed", "Submitted", "Closed"} for item in work
        ),
        "pending_review": sum(
            item.status in {"Submitted", "Awaiting Review"} for item in reports
        ),
        "critical_reports": sum(
            (item.ai_risk_score or 0) >= 70 for item in reports
        ),
        "open_critical_defects": sum(
            item.status == "Open" and item.severity == "Critical"
            for item in defects
        ),
        "overdue": overdue,
        "field_technicians": sum(
            item.role == "FIELD_TECHNICIAN" and item.active for item in users
        ),
        "coordinators": sum(
            item.role == "COORDINATOR" and item.active for item in users
        ),
        "sync_health": 100,
    }


@router.post("/assignments/{work_order_id}/start", response_model=WorkOrderOut)
def start_assignment(
    work_order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("FIELD_TECHNICIAN")),
) -> WorkOrder:
    work_order = db.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if work_order.assigned_user_id != user.id:
        raise HTTPException(status_code=403, detail="Assignment does not belong to this technician")
    if work_order.status == "Assigned":
        work_order.status = "In Progress"
        db.commit()
        db.refresh(work_order)
    return work_order


@router.get("/review-queue", response_model=list[ReportOut])
def review_queue(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")),
) -> list[InspectionReport]:
    return list(
        db.scalars(
            select(InspectionReport)
            .where(InspectionReport.status.in_(["Submitted", "Awaiting Review", "Returned"]))
            .order_by(InspectionReport.ai_risk_score.desc(), InspectionReport.submitted_at.desc())
        )
    )


@router.post("/reports/{report_id}/review", response_model=ReportOut)
def review_report(
    report_id: str,
    payload: ReviewDecision,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")),
) -> InspectionReport:
    report = db.get(InspectionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    work_order = db.get(WorkOrder, report.work_order_id)

    if payload.decision == "approve":
        report.status = "Approved"
        if work_order:
            work_order.status = "Completed"
    else:
        report.status = "Returned"
        if work_order:
            work_order.status = "In Progress"
        answers = dict(report.answers or {})
        answers["review_note"] = payload.note or "Returned for field correction."
        report.answers = answers

    db.add(report)
    if work_order:
        db.add(work_order)
    db.commit()
    db.refresh(report)
    return report
