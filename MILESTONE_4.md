# Milestone 4 — Commercial Configuration Layer

Milestone 4 moves TerraSync template/configuration data into the database.

## Added
- Clients and projects
- Database-backed inspection/survey templates
- Template draft/version/publish lifecycle
- Client/project asset schemas
- Configurable AI rule sets and thresholds
- Configurable report layouts and compression profiles
- Coordinator configuration views
- Seed migration from the Milestone 3 catalogue

The field app keeps using `/api/v1/inspection-templates`, so offline template caching remains compatible.
