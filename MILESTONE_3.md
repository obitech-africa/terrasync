# Milestone 3 — Configurable Inspection & Survey Templates

Milestone 3 adds a versioned template catalogue and dynamic field rendering.

## Included templates

### Telecommunications
- Telecom Tower Maintenance Inspection
- Rooftop Telecom Site Inspection
- Telecom Power & Shelter Inspection
- Telecom Site Survey

### Energy
- Solar PV Site Inspection
- Generator / Backup Power Inspection
- Solar Site Survey

### Utilities / Water / Agriculture
- Utility Asset Condition Survey
- Water / Pump Station Inspection
- Agriculture Infrastructure Survey

The tower-maintenance template is structurally based on the supplied ATC tower maintenance
references: site information, pre-climb, climb-up, tower-top, customer equipment inventory,
post-climb, corrections and summary.

Other sector templates use the same TerraSync architecture but are configurable product
templates rather than claims about requirements in the ATC documents.

## Template contract

Each template defines:
- sector
- inspection vs survey
- version
- sections
- field types
- required fields
- grading/options
- evidence rules
- minimum evidence count per section
- supported asset types

The field app downloads and caches template definitions for offline operation.

## Evidence

Inspection evidence remains live-camera-only.
Each inspection photo is associated with a template section and retains:
- GPS
- capture time
- location accuracy
- evidence UUID
- SHA-256
- compressed image content

Only GPS/time information is visibly watermarked on the photo.
