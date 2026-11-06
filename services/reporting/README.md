# TrackFlow Reporting Service

This directory defines the separate HTTP/service boundary for executive business reporting. It is distinct from `services/telemetry/` and `GET /telemetry/report`.

## Contract

- Business KPI aggregates are read from `reporting.executive_weekly_kpis`.
- Controlled refresh requests invoke the public pipeline interface under `data/pipelines/`; dependencies point from service to pipeline, never from pipeline back to service.
- The pipeline writes business aggregates only to the `reporting` schema, never to `telemetry_events`.
- Responses expose period, metric code/name, value and unit, dimensions, coverage status/reason, and generation/source freshness metadata. A blocked or unavailable metric is `null`, not zero.
- Customer-level dimensions require authorization and must not expose names, addresses, tracking numbers, free text, or other PII.

The route contract and outstanding implementation decisions are in [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md), sections 10 and **Phase 5 — Application integration**. The proposed business endpoints are:

- `GET /reporting/executive/status` → pipeline query function `get_executive_report_status(week_start)`; it reads `reporting.pipeline_runs` and persisted KPI status, never runs ETL.
- `POST /reporting/executive/weekly/refresh` → controlled dispatcher `request_executive_weekly_report(...)`, which invokes `executive_weekly_report_flow(...)` under `data/pipelines/`; authorization and idempotency are required.
- `GET /reporting/executive/weekly` → read function `get_executive_weekly_kpis(week_start)` for the Part 3 dashboard; persisted read only, not a recalculation.

All pipeline functions above are proposed interfaces, not currently implemented. `api.py` currently implements the weekly read directly against persisted aggregates. The M01 domain is TrackFlow shipments (`shipmentId`, `shipment_delivered`, `deliveredAt`, `promisedDate`, `onTime`) and eligible-shipment cohorts; if the authoritative full denominator is unavailable, report `metric_value: null` and `status: blocked`. These routes remain separate from `services/telemetry/` and `GET /telemetry/report`; no ETL logic belongs in the service. Refresh orchestration, database migrations, role grants, authentication/authorization and production scheduling remain unimplemented and must be completed before production use.
