
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect

from app.db.session import Base, engine

import app.models  # noqa: F401


class MigrationError(RuntimeError):
    """Raised when the database schema is not safe to use."""


@dataclass(frozen=True)
class MigrationStatus:
    current_revision: str | None
    head_revision: str
    has_application_tables: bool
    missing_tables: tuple[str, ...]
    up_to_date: bool


def alembic_config(database_engine: Engine = engine) -> Config:
    """Return Alembic configuration anchored to the backend directory."""
    backend_dir = Path(__file__).resolve().parents[2]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", str(database_engine.url).replace("%", "%%"))
    return config


def _head_revision(config: Config) -> str:
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    if not head:
        raise MigrationError("No Alembic head revision is configured.")
    return head


def _current_revision(database_engine: Engine) -> str | None:
    with database_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()


def migration_status(database_engine: Engine = engine) -> MigrationStatus:
    """Inspect the database without modifying it."""
    config = alembic_config(database_engine)
    head = _head_revision(config)
    inspector = inspect(database_engine)
    existing = set(inspector.get_table_names())
    application_tables = set(Base.metadata.tables)
    current = _current_revision(database_engine)
    missing = tuple(sorted(application_tables - existing))

    return MigrationStatus(
        current_revision=current,
        head_revision=head,
        has_application_tables=bool(existing & application_tables),
        missing_tables=missing,
        up_to_date=current == head and not missing,
    )


def bootstrap_legacy_database(database_engine: Engine = engine) -> MigrationStatus:
    """Adopt a pre-Alembic TerraSync database without deleting field data.

    Milestones 1-3 created tables through SQLAlchemy metadata. Milestone 4 adds
    additive configuration tables. The one-time bootstrap creates only missing
    tables, validates the resulting table set, then stamps the baseline revision.

    This command does not drop existing tables or rows.
    """
    status = migration_status(database_engine)
    if status.current_revision is not None:
        raise MigrationError(
            "Database is already managed by Alembic. Use `python -m app.db.migrate upgrade`."
        )
    if not status.has_application_tables:
        raise MigrationError(
            "Database is empty. Use `python -m app.db.migrate upgrade` instead."
        )

    Base.metadata.create_all(bind=database_engine)
    after_create = migration_status(database_engine)
    if after_create.missing_tables:
        raise MigrationError(
            "Legacy bootstrap could not create all required tables: "
            + ", ".join(after_create.missing_tables)
        )

    config = alembic_config(database_engine)
    command.stamp(config, "head")
    return migration_status(database_engine)


def upgrade_database(
    database_engine: Engine = engine,
    *,
    allow_legacy_bootstrap: bool = False,
) -> MigrationStatus:
    """Upgrade an empty or Alembic-managed database to the latest revision."""
    status = migration_status(database_engine)

    if status.current_revision is None and status.has_application_tables:
        if not allow_legacy_bootstrap:
            raise MigrationError(
                "Existing TerraSync tables are not yet tracked by Alembic. "
                "Run `python -m app.db.migrate bootstrap` once, then rerun upgrade."
            )
        bootstrap_legacy_database(database_engine)

    config = alembic_config(database_engine)
    command.upgrade(config, "head")
    return migration_status(database_engine)


def require_current_schema(database_engine: Engine = engine) -> MigrationStatus:
    """Fail fast when the production database is behind the code revision."""
    status = migration_status(database_engine)
    if not status.up_to_date:
        current = status.current_revision or "unversioned"
        missing = (
            f" Missing tables: {', '.join(status.missing_tables)}."
            if status.missing_tables
            else ""
        )
        raise MigrationError(
            f"Database schema is {current}; application expects {status.head_revision}."
            f"{missing} Run `python -m app.db.migrate upgrade` before starting the API."
        )
    return status
