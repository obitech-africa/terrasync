# Production Hardening Milestone

This overlay adds:

- PostgreSQL production enforcement
- Alembic-first deployment
- production configuration validation
- connection pool settings
- liveness/readiness probes
- structured JSON request logging
- request IDs
- non-root API container
- one-shot migration container
- PostgreSQL health checks
- API readiness health checks
- persistent PostgreSQL storage
- restart/graceful-stop policies
- PostgreSQL backup/restore scripts
- explicit CORS policy
- production documentation

SQLite remains the local/demo/test database.
