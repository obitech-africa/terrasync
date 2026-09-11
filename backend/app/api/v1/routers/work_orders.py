from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Site, WorkOrder
from app.schemas.domain import WorkOrderCreate, WorkOrderOut

router = APIRouter(prefix="/work-orders", tags=["work orders"])


@router.get("", response_model=list[WorkOrderOut])
def list_work_orders(db: Session = Depends(get_db)) -> list[WorkOrder]:
    return list(db.scalars(select(WorkOrder).order_by(WorkOrder.created_at.desc())))


@router.post("", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)) -> WorkOrder:
    if not db.get(Site, payload.site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    item = WorkOrder(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Work order number already exists") from exc
    db.refresh(item)
    return item
