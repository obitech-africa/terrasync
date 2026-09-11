from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.security import generate_token, hash_secret, token_fingerprint, verify_secret
from app.db.session import get_db
from app.models import ActivationCode, Device, User, WebSession
from app.schemas.auth import (
    ActivationCodeCreate,
    ActivationCodeIssued,
    AuthResponse,
    DeviceActivationRequest,
    StaffLoginRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@router.post("/activate-device", response_model=AuthResponse)
def activate_device(payload: DeviceActivationRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Consume a one-time code and permanently register one field device."""
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.active or user.role != "FIELD_TECHNICIAN":
        raise HTTPException(status_code=401, detail="Invalid activation credentials")

    codes = list(
        db.scalars(
            select(ActivationCode)
            .where(ActivationCode.user_id == user.id, ActivationCode.used_at.is_(None))
            .order_by(ActivationCode.created_at.desc())
        )
    )
    match = next(
        (
            item
            for item in codes
            if aware(item.expires_at) > utcnow() and verify_secret(payload.code, item.code_hash)
        ),
        None,
    )
    if not match:
        raise HTTPException(status_code=401, detail="Invalid or expired activation code")

    existing = db.scalar(select(Device).where(Device.device_key == payload.device_key))
    if existing and existing.active and existing.revoked_at is None:
        raise HTTPException(status_code=409, detail="This device is already registered")

    token = generate_token()
    if existing:
        existing.user_id = user.id
        existing.device_name = payload.device_name
        existing.platform = payload.platform
        existing.token_fingerprint = token_fingerprint(token)
        existing.active = True
        existing.revoked_at = None
        existing.activated_at = utcnow()
        existing.last_seen_at = utcnow()
        device = existing
    else:
        device = Device(
            user_id=user.id,
            device_name=payload.device_name,
            platform=payload.platform,
            device_key=payload.device_key,
            token_fingerprint=token_fingerprint(token),
        )
        db.add(device)

    match.used_at = utcnow()
    db.commit()
    db.refresh(device)
    return AuthResponse(
        access_token=token,
        user=UserOut.model_validate(user),
        device_id=device.id,
    )


@router.post("/staff-login", response_model=AuthResponse)
def staff_login(payload: StaffLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Authenticate coordinator, supervisor, or administrator dashboards."""
    user = db.scalar(select(User).where(User.username == payload.username))
    if (
        not user
        or not user.active
        or user.role not in {"COORDINATOR", "SUPERVISOR", "ADMIN"}
        or not user.password_hash
        or not verify_secret(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = generate_token()
    expires_at = utcnow() + timedelta(hours=12)
    db.add(
        WebSession(
            user_id=user.id,
            token_fingerprint=token_fingerprint(token),
            expires_at=expires_at,
        )
    )
    db.commit()
    return AuthResponse(
        access_token=token,
        user=UserOut.model_validate(user),
        expires_at=expires_at,
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/activation-codes", response_model=ActivationCodeIssued)
def issue_activation_code(
    payload: ActivationCodeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("COORDINATOR", "ADMIN")),
) -> ActivationCodeIssued:
    technician = db.get(User, payload.user_id)
    if not technician or technician.role != "FIELD_TECHNICIAN":
        raise HTTPException(status_code=404, detail="Field technician not found")

    code = f"{random.SystemRandom().randint(0, 999999):06d}"
    expires_at = utcnow() + timedelta(minutes=payload.expires_minutes)
    db.add(
        ActivationCode(
            user_id=technician.id,
            code_hash=hash_secret(code),
            expires_at=expires_at,
        )
    )
    db.commit()
    return ActivationCodeIssued(
        user_id=technician.id,
        code=code,
        expires_at=expires_at,
    )
