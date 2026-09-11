from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.migrations import require_current_schema, upgrade_database
from app.db.session import Base, SessionLocal, engine
from app.services.demo import seed_demo
from app.services.configuration_seed import seed_configuration

import app.models  # noqa: F401

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.ENVIRONMENT == "test":
        Base.metadata.create_all(bind=engine)
    elif settings.ENVIRONMENT in {"development", "demo"} and settings.AUTO_MIGRATE_DEVELOPMENT:
        upgrade_database(engine, allow_legacy_bootstrap=True)
    else:
        require_current_schema(engine)

    if settings.ENVIRONMENT in {"development", "demo"}:
        with SessionLocal() as db:
            seed_demo(db)
            seed_configuration(db)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Offline-first, AI-assisted field surveying, inspection and reporting API.",
    version="4.1.0-production-hardening",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

root_dir = Path(__file__).resolve().parents[2]
field_dir = root_dir / "field_app"
coordinator_dir = root_dir / "coordinator_dashboard"
supervisor_dir = root_dir / "supervisor_dashboard"

if field_dir.exists():
    app.mount(
        "/app",
        StaticFiles(directory=field_dir, html=True),
        name="field-app",
    )

if coordinator_dir.exists():
    app.mount(
        "/coordinator",
        StaticFiles(directory=coordinator_dir, html=True),
        name="coordinator-dashboard",
    )

if supervisor_dir.exists():
    app.mount(
        "/supervisor",
        StaticFiles(directory=supervisor_dir, html=True),
        name="supervisor-dashboard",
    )


@app.get("/")
def root():
    return {
        "name": "TerraSync API",
        "docs": "/docs",
        "field_app": "/app/",
        "coordinator": "/coordinator/",
        "supervisor": "/supervisor/",
    }
