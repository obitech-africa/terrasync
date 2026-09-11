# TerraSync production containers

## First deployment

Copy `.env.production.example` to `.env` and replace all example values.

```sh
docker compose build
docker compose run --rm migrate
docker compose up -d api
docker compose ps
```

The normal `docker compose up -d` flow also waits for PostgreSQL, runs the
one-shot migration service, and only starts the API after migrations succeed.

The API container never mutates the production schema during application
startup. Its startup check fails if the database revision is not current.

## Health

- Liveness: `/api/v1/health`
- Readiness: `/api/v1/ready`

## Backup

From `docker/`:

```sh
./scripts/backup-postgres.sh
```

## Restore

Stop API traffic before restoring:

```sh
docker compose stop api
./scripts/restore-postgres.sh ./backups/terrasync-YYYYMMDDTHHMMSSZ.dump
docker compose run --rm migrate
docker compose up -d api
```
