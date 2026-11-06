# TrackFlow Reporting Service

This directory defines the separate HTTP/service boundary for executive business reporting. It is distinct from `services/telemetry/` and `GET /telemetry/report`.

## Contract

- Business KPI aggregates are read from `reporting.executive_weekly_kpis`.
- Controlled refresh requests invoke the public pipeline interface under `data/pipelines/`; dependencies point from service to pipeline, never from pipeline back to service.
- The pipeline writes business aggregates only to the `reporting` schema, never to `telemetry_events`.
- Responses expose period, metric code/name, value and unit, dimensions, coverage status/reason, and generation/source freshness metadata. A blocked or unavailable metric is `null`, not zero.
- Customer-level dimensions require authorization and must not expose names, addresses, tracking numbers, free text, or other PII.

The route contract is in [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md), section 10. The implemented business endpoints are:

- `GET /reporting/executive/status` → `get_executive_report_status(week_start)` reads the latest restricted local pipeline JSONL audit record; it never runs ETL.
- `POST /reporting/executive/weekly/refresh` → `request_executive_weekly_report(...)` invokes the existing `executive_weekly_report_flow(...)` under `data/pipelines/`. It requires `X-Reporting-Operator-Key` to match the configured `REPORTING_OPERATOR_TOKEN`; the optional `Idempotency-Key` prevents duplicate dispatches for the same week/key.
- `GET /reporting/executive/weekly` → persisted read from `reporting.executive_weekly_kpis` for the Part 3 dashboard; no recalculation.

`GET /reporting/executive/weekly` reads the briefing schema directly from `reporting.executive_weekly_kpis` and returns period bounds plus metric rows (`metric_code`, `metric_name`, `definition_version`, `metric_value`, `unit`, `status`, `status_reason`, `dimensions`, `numerator`, `denominator`, `source_watermark`, `calculated_at`, `run_id`). The M01 domain is TrackFlow shipments (`shipmentId`, `shipment_delivered`, `deliveredAt`, `promisedDate`, `onTime`) and eligible-shipment cohorts; if the authoritative full denominator is unavailable, report `metric_value: null` and `status: blocked`. These routes remain separate from `services/telemetry/` and `GET /telemetry/report`; no ETL logic is duplicated in the service. Database migrations, least-privilege grants, production secret management, durable/shared run-log storage, and production scheduling still require operational review.
