#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup.dump>" >&2
  exit 2
fi

BACKUP="$1"

if [ ! -f "${BACKUP}" ]; then
  echo "Backup not found: ${BACKUP}" >&2
  exit 2
fi

cat "${BACKUP}" | docker compose exec -T postgres \
  pg_restore \
  --username="${POSTGRES_USER:-terrasync}" \
  --dbname="${POSTGRES_DB:-terrasync}" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl

echo "Restore completed from: ${BACKUP}"
