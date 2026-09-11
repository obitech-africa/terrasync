#!/usr/bin/env sh
set -eu

OUTPUT_DIR="${1:-./backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="${OUTPUT_DIR}/terrasync-${TIMESTAMP}.dump"

mkdir -p "${OUTPUT_DIR}"

docker compose exec -T postgres \
  pg_dump \
  --username="${POSTGRES_USER:-terrasync}" \
  --dbname="${POSTGRES_DB:-terrasync}" \
  --format=custom \
  --no-owner \
  --no-acl > "${FILE}"

echo "Backup created: ${FILE}"
