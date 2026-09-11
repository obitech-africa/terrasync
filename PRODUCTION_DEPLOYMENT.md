# TerraSync Production Deployment

TerraSync production deployments use PostgreSQL and Alembic-managed schema
revisions. SQLite remains supported for local development, demo and tests.

## Deployment sequence

Production deploys must follow this order:

1. build the application image;
2. start/check PostgreSQL;
3. run `python -m app.db.migrate upgrade`;
4. run `python -m app.db.migrate check`;
5. start API containers;
6. wait for `/api/v1/ready`;
7. route traffic to the API.

The API does not automatically mutate a production database schema.

## Environment

Copy `docker/.env.production.example` to `docker/.env`.

Replace:

- PostgreSQL password;
- public CORS origins;
- proxy allowlist;
- API bind address as required.

Do not commit `docker/.env`.

Production configuration rejects:

- SQLite database URLs;
- wildcard CORS;
- automatic development migrations.

## Docker deployment

From `docker/`:

```sh
docker compose build
docker compose up -d
docker compose ps
```

`migrate` is a one-shot service. The API service starts only if:

- PostgreSQL is healthy;
- migrations complete successfully.

The API binds to `127.0.0.1:8000` by default on the Docker host. Put TLS and
public ingress in front of it through a controlled reverse proxy/load balancer.

## Health model

`GET /api/v1/health`

Liveness only. It verifies that the application process can serve HTTP.

`GET /api/v1/ready`

Readiness verifies:

- database connectivity;
- current Alembic revision.

It returns HTTP 503 when TerraSync should not receive production traffic.

## Logging

Set:

```text
JSON_LOGS=true
LOG_LEVEL=INFO
```

Each HTTP response receives an `X-Request-ID`. Request logs include request ID,
HTTP method, path, status and duration.

If an upstream proxy provides request IDs, TerraSync preserves them.

## Database pooling

Production PostgreSQL tuning is controlled by:

```text
DB_POOL_SIZE
DB_MAX_OVERFLOW
DB_POOL_TIMEOUT_SECONDS
DB_POOL_RECYCLE_SECONDS
```

Tune pool capacity together with PostgreSQL `max_connections` and the number of
API replicas.

## Backup

From `docker/`:

```sh
./scripts/backup-postgres.sh
```

Backups use PostgreSQL custom dump format.

Copy backups off the application host according to the client's retention and
disaster-recovery policy.

## Restore

Before restoring:

1. remove API traffic;
2. stop API containers;
3. verify the intended backup;
4. restore;
5. rerun migrations;
6. check readiness;
7. restore traffic.

Example:

```sh
docker compose stop api
./scripts/restore-postgres.sh ./backups/terrasync-YYYYMMDDTHHMMSSZ.dump
docker compose run --rm migrate
docker compose up -d api
```

## Schema changes

After changing SQLAlchemy models:

```sh
cd backend
python -m alembic revision --autogenerate -m "describe_change"
```

Review the generated migration. Test it against PostgreSQL before merging.

Deployment then uses:

```sh
python -m app.db.migrate upgrade
python -m app.db.migrate check
```

## Secrets

Never commit:

- production `.env`;
- PostgreSQL passwords;
- third-party API keys;
- signing credentials;
- database backups containing client data.

Use the target platform's secret manager when deploying beyond a single-host
Docker environment.
