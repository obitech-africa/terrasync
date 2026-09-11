
from __future__ import annotations

import argparse

from app.db.migrations import (
    MigrationError,
    bootstrap_legacy_database,
    migration_status,
    require_current_schema,
    upgrade_database,
)


def print_status() -> None:
    status = migration_status()
    print(f"current_revision={status.current_revision or 'unversioned'}")
    print(f"head_revision={status.head_revision}")
    print(f"up_to_date={status.up_to_date}")
    if status.missing_tables:
        print("missing_tables=" + ",".join(status.missing_tables))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TerraSync database migration utility."
    )
    parser.add_argument(
        "command",
        choices=("status", "bootstrap", "upgrade", "check"),
    )
    args = parser.parse_args()

    try:
        if args.command == "status":
            print_status()
        elif args.command == "bootstrap":
            status = bootstrap_legacy_database()
            print(f"Bootstrapped legacy database at {status.current_revision}.")
        elif args.command == "upgrade":
            status = upgrade_database()
            print(f"Database upgraded to {status.current_revision}.")
        else:
            status = require_current_schema()
            print(f"Database schema is current at {status.current_revision}.")
    except MigrationError as exc:
        print(f"Migration error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
