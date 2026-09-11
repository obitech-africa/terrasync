from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import token_fingerprint
from app.db.session import get_db
from app.models import Device, User, WebSession


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve a field-device or staff bearer session."""
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    fingerprint = token_fingerprint(header.split(" ", 1)[1].strip())

    device = db.scalar(select(Device).where(Device.token_fingerprint == fingerprint))
    if device and device.active and device.revoked_at is None:
        user = db.get(User, device.user_id)
        if user and user.active:
            device.last_seen_at = utcnow()
            db.commit()
            return user

    session = db.scalar(select(WebSession).where(WebSession.token_fingerprint == fingerprint))
    if session and session.revoked_at is None:
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > utcnow():
            user = db.get(User, session.user_id)
            if user and user.active:
                return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid or expired")


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency
