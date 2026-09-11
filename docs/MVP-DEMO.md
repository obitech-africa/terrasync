# TerraSync MVP Demo

## Coordinator demo path

1. Start TerraSync and open `/app/`.
2. The seeded high-risk report demonstrates AI pre-screening immediately.
3. Open Reports and download its PDF.
4. Create a second inspection with safe readings to compare risk scoring.
5. Create an inspection while browser networking is disabled.
6. Verify the offline queue increments.
7. Restore networking and press Sync.
8. Verify the queued inspection receives a report number, AI findings and PDF export.

## Suggested risky readings

- Tower tilt: 2.4°
- Earth resistance: 7.0 Ω
- Safety condition: Unsafe
- Observations: `Severe corrosion and unsafe access area.`

These values intentionally trigger the MVP pre-screening rules.

## API demo

Interactive OpenAPI documentation is available at `/docs`.

Key endpoints:

- `GET /api/v1/sites`
- `GET /api/v1/work-orders`
- `POST /api/v1/reports`
- `POST /api/v1/reports/{id}/screen`
- `GET /api/v1/reports/{id}/findings`
- `GET /api/v1/reports/{id}/pdf`
- `POST /api/v1/sync/push`
- `GET /api/v1/sync/pull`
