# TerraSync Milestone 2

Milestone 2 connects the Milestone 1 role/device foundation to the field workflow and refreshes all three application surfaces.

## Working flow

1. Coordinator signs in and publishes an assignment.
2. Field technician activates a phone once with username + OTP.
3. The phone keeps its registered session and opens directly on later launches.
4. Assignments are cached locally.
5. Technician starts/continues an assignment.
6. Client-supplied inventory is downloaded when online.
7. Missing assets can be created on-site with manufacturer, model, serial, quantity, height/elevation, dimensions, position, condition and notes.
8. On-site assets require a live-camera full-picture capture.
9. Inspection drafts and the sync outbox are persisted in IndexedDB.
10. Evidence is captured by live camera, resized/compressed and watermarked with GPS + time only.
11. Asset changes synchronize before report submission.
12. Report sync is authenticated and idempotent.
13. Submission runs AI pre-screening.
14. Coordinator receives the report in the AI review queue and can approve or return it.
15. Supervisor dashboard reflects completion, pending review, critical reports and escalations.
16. PDF report generation remains available.

## Routes

- Field: `/app/`
- Coordinator: `/coordinator/`
- Supervisor: `/supervisor/`
- API: `/docs`

## Demo access

Field technician:
- username: `field.tech`
- activation code: `246810`

Coordinator:
- username: `coordinator`
- password: `demo123`

Supervisor:
- username: `supervisor`
- password: `demo123`

## Local database

The schema now includes the `assets` table. For a local SQLite demo, delete the old database before first launch of this build. Production should use Alembic migrations rather than dropping a database.

## Tested

- one-time device activation
- persistent device session
- RBAC
- coordinator assignment publication
- technician assignment receipt
- technician assignment start
- asset creation with assignment authorization
- report synchronization
- idempotency
- AI screening
- coordinator review
- supervisor metrics
- PDF generation
- JavaScript syntax
