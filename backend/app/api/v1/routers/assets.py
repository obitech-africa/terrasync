from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models import Asset, User, WorkOrder
from app.schemas.domain import AssetCreate, AssetOut

router = APIRouter(prefix="/assets", tags=["assets"])


def _validate_work_order_access(db: Session, user: User, work_order_id: str) -> WorkOrder:
    work_order = db.get(WorkOrder, work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="Work order not found")
    if user.role == "FIELD_TECHNICIAN" and work_order.assigned_user_id != user.id:
        raise HTTPException(status_code=403, detail="Assignment does not belong to this technician")
    return work_order


@router.get("", response_model=list[AssetOut])
def list_assets(
    work_order_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Asset]:
    stmt = select(Asset).order_by(Asset.created_at)
    if work_order_id:
        _validate_work_order_access(db, user, work_order_id)
        stmt = stmt.where(Asset.work_order_id == work_order_id)
    elif user.role == "FIELD_TECHNICIAN":
        assigned_ids = select(WorkOrder.id).where(WorkOrder.assigned_user_id == user.id)
        stmt = stmt.where(Asset.work_order_id.in_(assigned_ids))
    elif user.role not in {"COORDINATOR", "SUPERVISOR", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return list(db.scalars(stmt))


@router.post("", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Asset:
    existing = db.scalar(select(Asset).where(Asset.client_id == payload.client_id))
    if existing:
        return existing
    work_order = _validate_work_order_access(db, user, payload.work_order_id)
    if work_order.site_id != payload.site_id:
        raise HTTPException(status_code=422, detail="Asset site does not match assignment")
    data = payload.model_dump()
    data["evidence"] = [item.model_dump(mode="json") for item in payload.evidence]
    asset = Asset(**data, created_by_user_id=user.id)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
