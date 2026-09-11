
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db.migrations import migration_status
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Liveness probe: process is running and routing requests."""
    return {
        "status": "ok",
        "service": "TerraSync API",
    }


@router.get("/ready")
def readiness_check(response: Response):
    """Readiness probe: database is reachable and schema is current."""
    database_ok = False
    schema_ok = False
    revision = None
    head = None
    error = None

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ok = True

        migration = migration_status(engine)
        schema_ok = migration.up_to_date
        revision = migration.current_revision
        head = migration.head_revision
    except Exception as exc:
        error = str(exc)

    ready = database_ok and schema_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if ready else "not_ready",
        "database": "ok" if database_ok else "unavailable",
        "schema": "current" if schema_ok else "out_of_date",
        "current_revision": revision,
        "head_revision": head,
        "error": error,
    }
