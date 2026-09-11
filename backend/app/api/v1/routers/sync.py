from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import ChangeEvent, InspectionReport, User, WorkOrder
from app.schemas.domain import SyncPullResponse, SyncPushRequest, SyncPushResponse, SyncMutationResult
from app.api.v1.routers.reports import create_or_get_report

router = APIRouter(prefix="/sync", tags=["offline sync"])


def current_cursor(db: Session) -> int:
    return int(db.scalar(select(func.max(ChangeEvent.id))) or 0)


@router.post("/push", response_model=SyncPushResponse)
def push(
    payload: SyncPushRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SyncPushResponse:
    """Apply queued client mutations idempotently using each report's client-generated ID."""
    results: list[SyncMutationResult] = []
    for mutation in payload.mutations:
        work_order = db.get(WorkOrder, mutation.payload.work_order_id)
        if not work_order:
            results.append(
                SyncMutationResult(
                    mutation_id=mutation.mutation_id,
                    status="error",
                    message="Work order not found",
                )
            )
            continue
        if user.role == "FIELD_TECHNICIAN" and work_order.assigned_user_id != user.id:
            results.append(
                SyncMutationResult(
                    mutation_id=mutation.mutation_id,
                    status="error",
                    message="Assignment does not belong to this technician",
                )
            )
            continue

        existing = db.scalar(
            select(InspectionReport).where(InspectionReport.client_id == mutation.payload.client_id)
        )
        if existing:
            results.append(
                SyncMutationResult(
                    mutation_id=mutation.mutation_id,
                    status="duplicate",
                    entity_id=existing.id,
                    message="Already synchronized",
                )
            )
            continue
        try:
            report = create_or_get_report(db, mutation.payload)
            if mutation.payload.submit:
                work_order.status = "Submitted"
                db.add(work_order)
                db.commit()
            results.append(
                SyncMutationResult(
                    mutation_id=mutation.mutation_id,
                    status="applied",
                    entity_id=report.id,
                )
            )
        except Exception as exc:
            db.rollback()
            results.append(
                SyncMutationResult(
                    mutation_id=mutation.mutation_id,
                    status="error",
                    message=str(exc),
                )
            )
    return SyncPushResponse(results=results, cursor=current_cursor(db))


@router.get("/pull", response_model=SyncPullResponse)
def pull(
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SyncPullResponse:
    changes = list(
        db.scalars(
            select(ChangeEvent)
            .where(ChangeEvent.id > cursor)
            .order_by(ChangeEvent.id)
            .limit(limit)
        )
    )
    next_cursor = changes[-1].id if changes else cursor
    return SyncPullResponse(
        cursor=next_cursor,
        changes=[
            {
                "id": item.id,
                "entity": item.entity_type,
                "entity_id": item.entity_id,
                "operation": item.operation,
                "payload": item.payload,
                "created_at": item.created_at.isoformat(),
            }
            for item in changes
        ],
    )
