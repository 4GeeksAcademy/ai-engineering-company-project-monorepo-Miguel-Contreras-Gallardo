# TrackFlow Reporting Service

This directory defines the separate HTTP/service boundary for executive business reporting. It is distinct from `services/telemetry/` and `GET /telemetry/report`.

## Contract

- Business KPI aggregates are read from `reporting.executive_weekly_kpis`.
- Controlled refresh requests invoke the public pipeline interface under `data/pipelines/`; dependencies point from service to pipeline, never from pipeline back to service.
- The pipeline writes business aggregates only to the `reporting` schema, never to `telemetry_events`.
- Responses expose period, metric code/name, value and unit, dimensions, coverage status/reason, and generation/source freshness metadata. A blocked or unavailable metric is `null`, not zero.
- Customer-level dimensions require authorization and must not expose names, addresses, tracking numbers, free text, or other PII.

The proposed route contract and outstanding implementation decisions are in [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md), section 10. This directory is a design scaffold only; no endpoint is active until its database access, authentication, migration, and FastAPI integration are implemented and tested.
