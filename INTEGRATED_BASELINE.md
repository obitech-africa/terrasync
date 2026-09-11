# TerraSync Integrated Baseline — Milestones 1 + 2

This repository is the consolidated TerraSync project baseline.

## Included from Milestone 1

- Server-side staff authentication
- One-time technician device activation
- Persistent registered-device sessions
- Role-based access control
- Field Technician, Coordinator, Supervisor and Administrator roles
- Technician profile and certification metadata
- Device registration/revocation
- Assignment ownership and publication
- Coordinator dashboard
- Supervisor dashboard

## Included from Milestone 2

- Technician assignment start/continue workflow
- Offline-first field app shell
- IndexedDB-backed drafts/outbox
- Authenticated idempotent synchronization
- Client-supplied and on-site-created equipment inventory
- Live-camera-only evidence
- GPS/time evidence watermark
- Evidence hashing/compression
- AI pre-screening integration
- Coordinator approve/return workflow
- Supervisor escalation/portfolio visibility
- PDF reporting integration

## Product surfaces

- Field Technician: `/app/`
- Coordinator: `/coordinator/`
- Supervisor: `/supervisor/`
- FastAPI docs: `/docs`

## Local demo

From `backend/`:

```powershell
python -m pip install -r requirements.txt
Remove-Item .\terrasync.db -ErrorAction SilentlyContinue
uvicorn app.main:app --reload
```

Demo access:

- Field technician: `field.tech` + one-time code `246810`
- Coordinator: `coordinator` / `demo123`
- Supervisor: `supervisor` / `demo123`

The field activation code is consumed once. A successfully registered device opens the field app without requiring the technician to enter credentials on every launch.

## Validation

- Backend test suite: 12 passed
- Python compilation: passed
- Field app JavaScript syntax: passed
- Coordinator JavaScript syntax: passed
- Supervisor JavaScript syntax: passed
- Legacy dashboard JavaScript syntax: passed
