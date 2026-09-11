# TerraSync — Milestone 2

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


---

# TerraSync MVP

TerraSync is an offline-first, AI-assisted field surveying, inspection and reporting platform.

## What works in this MVP

- FastAPI REST backend with SQLite for zero-config demos and PostgreSQL for Docker deployments.
- Sites, work orders, inspection reports, defects, AI findings and change events persisted with SQLAlchemy.
- Installable responsive PWA served by the backend.
- Offline app shell plus a persistent local outbox for inspection submissions.
- Idempotent push sync and cursor-based pull sync.
- Conflict detection through report revisions.
- Local hybrid AI/rules pre-screening for completeness, inconsistent values, abnormal readings, safety risks and critical conditions.
- Human-review oriented AI findings and risk score.
- PDF report generation including inspection data, AI findings and evidence manifest.
- Demo seed data and automated end-to-end tests.

## Fastest demo

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- App: http://localhost:8000/app/
- API docs: http://localhost:8000/docs

The default database is `backend/terrasync.db` and demo data is created automatically.
## Reliable Field Operations. Anywhere.

**Survey. Inspect. Verify. Report. Even Offline.**

TerraSync is an **offline-first, AI-assisted field surveying, inspection, evidence, and reporting platform** designed for organizations whose teams operate in environments where connectivity cannot always be guaranteed.

Powered by a **Python/FastAPI backend** and a Flutter mobile application, TerraSync enables field engineers, technicians, surveyors, inspectors, coordinators, and supervisors to receive work orders, conduct structured surveys and inspections, capture verifiable field evidence, record measurements and defects, generate professional reports, and securely synchronize field data when connectivity becomes available.

Telecommunications is TerraSync's first reference implementation, but the underlying field operations engine is designed to support utilities, energy, water, construction, transport, healthcare, agriculture, mining, oil and gas, government infrastructure, and other sectors that depend on reliable field data.

---

# Why TerraSync?

Field operations frequently take place in locations where internet connectivity is weak, intermittent, expensive, or completely unavailable.

Many organizations still depend on combinations of:

* Paper inspection forms
* Spreadsheets
* Messaging applications
* Disconnected photographs
* Manual GPS recording
* Separate survey documents
* Delayed reporting
* Manual defect identification
* Fragmented approval processes

This makes it difficult to verify what happened in the field, where it happened, when it happened, and whether the submitted information is complete.

TerraSync brings these activities into one structured field operations workflow.

```text
Work Order
    ↓
Site Check-In
    ↓
Safety Readiness
    ↓
Survey / Inspection
    ↓
Checklist + Measurements
    ↓
Verified Photo Evidence
    ↓
Remarks + Defects
    ↓
Report Generation
    ↓
Offline Save
    ↓
Secure Synchronization
    ↓
AI-Assisted Pre-Review
    ↓
Coordinator Review
    ↓
Approval / Return for Correction
```

---

# Core Features

## Offline-First Field Operations

TerraSync is designed to continue functioning when internet connectivity is unavailable.

Field teams can:

* Access assigned work
* Check into sites
* Complete surveys
* Conduct inspections
* Record measurements
* Capture photographs
* Record remarks
* Identify defects
* Generate field reports
* Save completed work locally

Once connectivity becomes available, TerraSync securely synchronizes pending information with the central platform.

---

## Work Order Management

Organizations can create and assign structured work orders to field personnel.

A work order can contain:

* Work Order ID
* Site ID
* Site name
* Location
* Assigned technician or team
* Activity type
* Required report/template
* Priority
* Scheduled date
* Instructions
* Current status

Work orders provide the operational link between management and field execution.

---

# Surveying

Surveying is a core TerraSync capability.

The surveying workflow can be configured to capture:

* Site coordinates
* Location information
* Site conditions
* Measurements
* Dimensions
* Existing infrastructure
* Equipment and asset inventory
* Access conditions
* Power availability
* Environmental observations
* Proposed installation locations
* Photographic evidence
* Surveyor remarks
* Risks and constraints
* Recommendations

Survey templates can be adapted for telecom site surveys, construction surveys, utilities, roads, energy projects, agriculture, infrastructure assessments, and other field operations.

---

# Template-Driven Field Operations

TerraSync uses a reusable **template engine** rather than hard-coding every field operation into the application.

Templates define:

* Sections
* Inspection items
* Survey questions
* Checklists
* Measurements
* Required evidence
* Validation rules
* Defect categories
* Conditional questions
* Report structure

This allows organizations to create different field workflows without rebuilding the TerraSync application.

```text
TerraSync Field Engine
│
├── Survey Templates
├── Inspection Templates
├── Maintenance Templates
├── Acceptance Templates
├── Audit Templates
└── Verification Templates
```

---

# Standard Inspection Item

Every inspection item follows a consistent structure.

```text
Inspection Item
│
├── Status
├── Measurement (if applicable)
├── Capture Photo
├── Remarks / Description
└── Defect Details (if required)
```

Depending on the template, an inspection item can support:

* Pass / Fail
* Good / Fair / Poor
* Yes / No
* Numeric measurements
* Text observations
* Multiple-choice responses
* Required photographs
* Defect severity
* Corrective recommendations

---

# Verified Field Evidence

Photos in TerraSync are treated as **evidence belonging to the report**, not as independent photo records.

Evidence is captured directly from the field workflow.

Each field photo automatically records:

* GPS coordinates
* Timestamp
* Site ID

This creates a direct relationship between:

```text
Site
   ↓
Work Order
   ↓
Report
   ↓
Inspection / Survey Item
   ↓
Photo Evidence
```

This helps organizations understand exactly what each photograph proves and where it belongs within the report.

---

# Safety Readiness

Before beginning certain field activities, TerraSync can require a structured safety and readiness check.

This can include:

* Check-in time
* PPE confirmation
* First-aid kit verification
* Tools and equipment verification
* Team readiness
* Health/readiness confirmation
* Safety observations
* Required safety photographs

Organizations can configure safety requirements according to the activity being performed.

---

# Remarks and Defects

Remarks can be recorded at multiple levels of a field operation.

```text
Report
├── Section
│   ├── Inspection Item
│   │   ├── Status
│   │   ├── Measurement
│   │   ├── Photo
│   │   ├── Remark
│   │   └── Defect
```

A defect can contain:

* Defect type
* Description
* Severity
* Related inspection item
* Measurement
* Photo evidence
* Recommended corrective action
* Technician remarks

This allows TerraSync to maintain the context surrounding every identified issue.

---

# AI-Assisted Coordinator Review

TerraSync introduces AI at the **coordinator/supervisor review level**.

After a field report has successfully synchronized, the platform can automatically pre-screen the report before the coordinator begins the full manual review.

The AI assistant can identify:

* Missing required information
* Incomplete inspection sections
* Missing required evidence
* Contradictory responses
* Abnormal measurements
* Potential data inconsistencies
* Repeated or unusual readings
* Safety concerns
* Potentially critical defects
* Items requiring coordinator attention

The coordinator can therefore receive a summary such as:

```text
AI PRE-REVIEW

Report completeness: 94%

Potential Issues: 4

HIGH PRIORITY
• Tower member marked damaged
• Earthing measurement outside configured threshold

REVIEW REQUIRED
• Generator section missing required evidence
• Battery voltage reading appears abnormal

Recommendation:
Manual review required before approval.
```

AI acts as a **decision-support system**.

It does not replace the coordinator and does not automatically approve reports.

The final decision remains with an authorized human reviewer.

---

# Operational Roles

TerraSync is designed around three primary operational layers.

## 1. Field Technician / Surveyor

The field application enables technicians and surveyors to:

* Receive work orders
* Access assigned sites
* Check in
* Complete safety checks
* Conduct surveys
* Perform inspections
* Record measurements
* Capture evidence
* Record remarks and defects
* Generate reports
* Work offline
* Synchronize completed work

---

## 2. Coordinator / Supervisor

The coordinator interface provides visibility into synchronized field operations.

Coordinators can:

* Monitor submitted reports
* View AI pre-review findings
* Review measurements
* Inspect field evidence
* Review defects
* Identify critical issues
* Return reports for correction
* Add review comments
* Approve completed reports
* Monitor field performance

Reports that remain offline and unsynchronized on a technician's device are **not considered submitted** and therefore do not appear as submitted reports on the coordinator dashboard.

---

## 3. Administrator

Administrators manage the TerraSync environment.

Administration capabilities can include:

* Organizations
* Users
* Roles
* Permissions
* Sites
* Assets
* Templates
* Workflows
* Work orders
* Defect classifications
* Approval rules
* Reporting configuration
* System settings
* Audit logs

---

# Telecom Reference Implementation

Telecommunications is the first complete reference implementation for TerraSync.

The initial telecom template library includes:

1. Site Survey Report
2. Tower Inspection Report
3. Power Inspection Report
4. RMS Report
5. Preventive Maintenance Report
6. Corrective Maintenance Report
7. Transmission Inspection Report
8. Shelter Inspection Report
9. Site Acceptance Report

Additional templates can be introduced without changing the core field operations engine.

## PostgreSQL demo

```bash
cd docker
docker compose up --build
```

Then open http://localhost:8000/app/.

## Offline demonstration

1. Open the app while online once.
2. Open **New inspection**.
3. Use browser devtools to switch the network to Offline.
4. Submit an inspection. It remains in the local outbox.
5. Re-enable network access and press **Sync**.
6. Open **Reports** to see the server AI risk score and download the generated PDF.

## AI safety model

The MVP intentionally uses a local deterministic pre-screening engine. It never autonomously approves reports. It flags issues for a human coordinator and works without internet access. The engine is designed to be replaced or augmented by a model provider later while preserving the same `AIFinding` contract.

## Production gaps after MVP

Authentication/authorization, encrypted evidence object storage, signed evidence provenance, background job processing, schema migrations, richer template authoring, device enrollment, telemetry, and production-grade observability remain follow-on work.
# Telecom Site Survey

The telecom surveying workflow can capture information such as:

* Site ID
* GPS coordinates
* Site accessibility
* Tower information
* Tower height
* Existing equipment
* Antenna inventory
* Microwave dish inventory
* Transmission equipment
* Power infrastructure
* Battery systems
* Generator information
* Solar equipment
* Earthing infrastructure
* Shelter condition
* Cable routing
* Available installation space
* Proposed equipment locations
* Photographic evidence
* Survey findings
* Recommendations

This gives organizations a structured view of a site before deployment, upgrade, maintenance, or acceptance activities.

---

# Reporting

TerraSync converts structured field data into professional reports.

Reports can contain:

* Organization information
* Work order information
* Site information
* Technician/surveyor information
* Check-in details
* GPS information
* Safety readiness
* Survey findings
* Inspection results
* Measurements
* Photo evidence
* Remarks
* Defects
* Recommendations
* AI pre-review findings
* Coordinator comments
* Approval status

Supported export formats can include:

* PDF
* Excel

---

# Offline-First Architecture

TerraSync is designed around local-first data capture.

```text
┌───────────────────────┐
│ Flutter Mobile App    │
│ Technician / Surveyor │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ SQLite Local Database │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Offline Sync Queue    │
└───────────┬───────────┘
            │
      Connectivity
        Available
            │
            ▼
┌───────────────────────┐
│ FastAPI Backend       │
│ Python                │
└───────────┬───────────┘
            │
       ┌────┴────┐
       ▼         ▼
 PostgreSQL     Redis
       │
       ▼
┌───────────────────────┐
│ AI Pre-Review Engine  │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Operations Dashboard  │
│ Coordinator / Admin   │
└───────────────────────┘
```

---

# Synchronization Model

The mobile application maintains a local synchronization queue.

```text
Draft
  ↓
Completed Locally
  ↓
Pending Sync
  ↓
Uploading
  ↓
Synchronized
  ↓
Submitted
  ↓
AI Pre-Review
  ↓
Coordinator Review
  ↓
Approved
      or
Returned for Correction
```

A locally completed report is not treated as centrally submitted until synchronization has completed successfully.

This prevents management dashboards from displaying field information that has not yet reached the central system.

---

# Technology Stack

| Layer              | Technology                  |
| ------------------ | --------------------------- |
| Mobile Application | Flutter                     |
| Backend API        | Python + FastAPI            |
| Local Database     | SQLite                      |
| Central Database   | PostgreSQL                  |
| Queue / Cache      | Redis                       |
| Deployment         | Docker                      |
| Reporting          | PDF / Excel                 |
| Mapping / GIS      | GIS integration             |
| AI Layer           | AI-assisted report analysis |
| Version Control    | GitHub                      |

---

# Cross-Sector Applications

TerraSync's underlying field operations engine is sector-independent.

The same platform can support:

### Telecommunications

Tower inspections, site surveys, maintenance, transmission, power systems, acceptance and infrastructure audits.

### Utilities & Energy

Power infrastructure inspections, substations, transformers, distribution assets and maintenance operations.

### Renewable Energy

Solar installations, battery systems, mini-grids, commissioning and preventive maintenance.

### Water & Wastewater

Pipelines, pumping stations, treatment facilities, meters and infrastructure assessments.

### Construction

Site inspections, progress verification, quality assurance and safety assessments.

### Roads & Bridges

Road-condition surveys, bridge inspections, drainage assessments and maintenance reporting.

### Rail & Transport

Track infrastructure, stations, transport assets and maintenance operations.

### Healthcare Facilities

Facility inspections, equipment audits, infrastructure assessments and compliance checks.

### Agriculture

Farm surveys, irrigation infrastructure, crop observations and field assessments.

### Mining

Equipment inspections, infrastructure surveys, environmental observations and safety assessments.

### Oil & Gas

Pipeline inspections, facility maintenance, equipment verification and safety reporting.

### Government Infrastructure

Public asset surveys, infrastructure monitoring, inspections and project verification.

The core principle remains:

**One offline-first field operations engine. Many industries.**

---

# Roadmap

## Phase 1 — Foundation

Build the reliable core field platform.

* Flutter mobile application
* Python/FastAPI backend
* Offline data capture
* SQLite local database
* PostgreSQL central database
* Inspection templates
* Survey templates
* Safety workflow
* Photo evidence
* GPS and timestamp capture
* Remarks and defects
* Synchronization engine
* Basic report generation
* Telecom reference implementation

---

## Phase 2 — Operations & Assisted Review

Introduce centralized operational management and initial intelligence.

* Work order management
* Coordinator dashboard
* Administrator dashboard
* Template builder
* GIS/map integration
* Alerts and notifications
* AI-assisted report pre-screening
* Completeness checking
* Measurement anomaly detection
* Missing-evidence detection
* Defect prioritization
* Review and approval workflows

---

## Phase 3 — Intelligence

Expand TerraSync's analytical capabilities.

* AI-assisted visual defect detection
* Condition scoring
* Asset health scoring
* Historical trend analysis
* Predictive maintenance
* Advanced anomaly detection
* Risk identification
* Advanced operational analytics

---

## Phase 4 — Enterprise Scale

Prepare TerraSync for large organizations.

* Multi-tenant organizations
* Enterprise administration
* Advanced permissions
* Organization-specific templates
* Advanced audit trails
* API integrations
* High availability
* Enterprise security
* Large-scale deployment support

---

## Phase 5 — Ecosystem

Develop TerraSync into an extensible field operations ecosystem.

* Plugin architecture
* Community templates
* Third-party integrations
* Public API
* Developer documentation
* Sector template libraries
* Integration marketplace
* Global open-source community

---

# Open-Source Vision

TerraSync is being designed as an open-source project because reliable field operations technology should be accessible, transparent, adaptable, and capable of working in environments where conventional cloud-only systems struggle.

The project can welcome contributions in:

* Python backend development
* Flutter mobile development
* Offline synchronization
* Database architecture
* AI-assisted analysis
* UX/UI design
* GIS
* Reporting
* Testing
* Documentation
* Telecom engineering templates
* Surveying workflows
* Cross-sector field templates

The open architecture also allows organizations to adapt TerraSync to their operational requirements rather than forcing every organization into a single predefined workflow.

---

# Project Status

TerraSync is currently in **concept, system design, and prototype preparation**, with its initial reference implementation being prepared around telecommunications field operations and the PyCon Africa 2026 presentation.

Current project materials include:

* Technical architecture
* Mobile application concepts
* Coordinator dashboard concepts
* Administrator dashboard concepts
* Inspection workflow design
* Surveying workflow design
* Telecom template definitions
* Offline synchronization architecture
* AI-assisted review concept
* 15-slide technical presentation
* A0 PyCon Africa poster
* One-page technical brief
* Architecture diagrams
* Mobile and dashboard UI mockups
* Demo workflow
* Speaker notes

---

# Design Principles

TerraSync development follows several core principles:

**Offline First**
A field operation should not stop simply because internet connectivity disappears.

**Evidence by Design**
Photographs, measurements, location and observations should remain connected to the field activity they verify.

**Structured, Not Fragmented**
Field information should move through one structured workflow rather than being distributed across paper, spreadsheets, messaging applications and photo galleries.

**Human-Controlled AI**
AI assists coordinators by identifying issues and prioritizing attention, while authorized personnel retain responsibility for operational decisions and report approval.

**Reusable Architecture**
The same field engine should support multiple industries through configurable templates.

**Field Reality First**
TerraSync should be designed around the realities of engineers, technicians, inspectors and surveyors working in difficult environments.

---

# Vision

TerraSync aims to become a reusable digital infrastructure layer for field operations.

Instead of organizations building separate applications for surveying, inspection, maintenance, evidence collection, reporting and field verification, TerraSync brings these activities together through one configurable platform.

```text
                 TERRASYNC
                     │
       Offline-First Field Engine
                     │
       ┌─────────────┼─────────────┐
       │             │             │
    Survey        Inspect       Maintain
       │             │             │
       └─────────────┼─────────────┘
                     │
                  Verify
                     │
                  Report
                     │
               AI Pre-Review
                     │
                Human Review
                     │
              Operational Data
                     │
                 Analytics
```

The long-term goal is simple:

> **Make reliable field data possible anywhere — regardless of connectivity, geography, or industry.**

---

# License

The open-source license will be confirmed before the first public release.

---

# TerraSync

**Reliable Field Operations. Anywhere.**

**Survey. Inspect. Verify. Report. Even Offline.**
