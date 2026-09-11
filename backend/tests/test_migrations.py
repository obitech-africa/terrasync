
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.db.migrations import (
    bootstrap_legacy_database,
    migration_status,
    require_current_schema,
    upgrade_database,
)
from app.db.session import Base

import app.models  # noqa: F401


M4_TABLES = {
    "clients",
    "projects",
    "template_definitions",
    "template_versions",
    "asset_schemas",
    "ai_rule_sets",
    "report_layouts",
}


def sqlite_engine(tmp_path: Path, name: str):
    return create_engine(
        f"sqlite:///{(tmp_path / name).as_posix()}",
        connect_args={"check_same_thread": False},
    )


def test_alembic_upgrade_empty_database_to_head(tmp_path):
    database = sqlite_engine(tmp_path, "empty.db")

    status = upgrade_database(database)

    assert status.up_to_date is True
    assert status.current_revision == status.head_revision
    tables = set(inspect(database).get_table_names())
    assert set(Base.metadata.tables).issubset(tables)
    assert "alembic_version" in tables


def test_bootstrap_legacy_database_preserves_existing_rows(tmp_path):
    database = sqlite_engine(tmp_path, "legacy.db")
    legacy_tables = [
        table
        for name, table in Base.metadata.tables.items()
        if name not in M4_TABLES
    ]
    Base.metadata.create_all(bind=database, tables=legacy_tables)

    with database.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (
                    id, username, full_name, role, certifications, active, created_at
                )
                VALUES (
                    'legacy-user', 'legacy.tech', 'Legacy Technician',
                    'field_technician', '[]', 1, CURRENT_TIMESTAMP
                )
                """
            )
        )

    before = migration_status(database)
    assert before.current_revision is None
    assert before.has_application_tables is True
    assert M4_TABLES.intersection(before.missing_tables)

    after = bootstrap_legacy_database(database)

    assert after.up_to_date is True
    assert not after.missing_tables
    with database.connect() as connection:
        username = connection.execute(
            text("SELECT username FROM users WHERE id = 'legacy-user'")
        ).scalar_one()
    assert username == "legacy.tech"


def test_production_schema_check_accepts_current_database(tmp_path):
    database = sqlite_engine(tmp_path, "current.db")
    upgrade_database(database)

    status = require_current_schema(database)

    assert status.up_to_date is True
