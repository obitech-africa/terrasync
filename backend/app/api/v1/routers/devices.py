from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models import Device, User
from app.schemas.auth import DeviceOut

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "SUPERVISOR", "ADMIN")),
) -> list[Device]:
    return list(db.scalars(select(Device).order_by(Device.last_seen_at.desc())))


@router.post("/{device_id}/revoke", response_model=DeviceOut)
def revoke_device(
    device_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("SUPERVISOR", "ADMIN")),
) -> Device:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.active = False
    device.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(device)
    return device
