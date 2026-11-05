# Executive Reporting Pipeline — Design

**Status:** Design proposal. KPI and destination contract: [`company-BRIEFING.md`](./company-BRIEFING.md).

## 1. Goal and boundaries

Produce a governed weekly executive report for TrackFlow, with an extensible refresh path for dashboards. The pipeline combines authoritative operational source data with mandatory telemetry signals where relevant, validates coverage, computes reproducible KPI aggregates, and writes only to PostgreSQL `reporting.executive_weekly_kpis`.

The report is separate from the technical telemetry report at `GET /telemetry/report`. That endpoint remains focused on technical event metrics. This pipeline does not write to `telemetry_events` and does not treat telemetry events as complete business ledgers when the KPI contract requires a full source universe.

## 2. Dependency direction and repository placement

```text
source systems / telemetry store
              │
              ▼
data/raw/                 landing/adapters; restricted, transient where possible
              │
              ▼
data/process/reporting/   pure, reusable parsing, validation and KPI transforms
              ▲
              │ imported by
 data/pipelines/executive_report/  orchestration, scheduling, retries, persistence
              ▲
              │ invoked by
 services/reporting/      HTTP/API boundary for read and controlled refresh operations
```

- Orchestration, connectors, scheduling and load coordination belong under `data/pipelines/` (proposed package: `data/pipelines/executive_report/`).
- Deterministic, reusable transformations belong under `data/process/` (proposed package: `data/process/reporting/`). They should accept explicit inputs and return typed records/data frames; no HTTP, scheduler or database connection side effects in pure transform functions.
- `services/reporting/` is a distinct reporting service/module. It may invoke pipeline entry points and read the reporting product. It must not be folded into `services/telemetry/` or the technical telemetry report route.
- **Dependency rule:** services may import pipeline interfaces; pipelines/process must never import from `services/`.
- This document creates no runtime scheduler or database client. Select the production scheduler and source connectors when credentials, deployment topology and source ownership are known. n8n is mentioned as the project-level workflow option, not assumed as an installed dependency.

## 3. Sources and source contracts

1. **Operational systems of record** (to be integrated): shipment/order cohort and delivery promises, warehouse picking assignment/start/completion, returns, CX ticket universe, carrier invoices/settlements and billable weights, deployment approvals/releases, incident SLA lifecycle, inventory ledger/transitions, and B2B satisfaction survey responses.
2. **Telemetry store**: events and freshness signals described in `docs/telemetry/event-schemas.json` and `docs/telemetry/telemetry-plan.md`. Use only events whose schema and producer are actually present. Telemetry can contribute observations, but it is not a replacement for source-of-truth denominators/ledgers.
3. **Current project data**: the repository contains an inventory API and telemetry infrastructure, but not all operational source integrations needed for M01–M10. The first implementation phase should inspect deployed schemas and agree source owners/contracts before enabling each KPI.

For each input define owner, schema/version, event or transaction time, ingestion/update time, primary key, late-arrival behavior, deletion/correction behavior, timezone, retention and PII classification. Reject or quarantine malformed records; do not silently coerce unknown event versions or units.

## 4. Proposed stages

1. **Extract** incrementally from approved sources using a stable cursor/watermark. Persist source/run metadata and raw payload only when needed for replay, with restricted access and retention. Avoid committing production data to `data/raw/`.
2. **Normalize** timestamps to UTC; normalize units/currency with an explicit conversion source and effective time; map country, warehouse, carrier and opaque entity IDs through controlled dimensions.
3. **Validate** required fields, primary-key uniqueness, referential joins, event allowlists, temporal ordering, cohort completeness and source watermarks. Track rejected records and validation counts without leaking raw PII.
4. **Transform** into KPI-specific numerator/denominator components at the declared cohort and grain. Implement transformations in `data/process/reporting/`; include definition version and explicit `available`/`partial`/`blocked` state.
5. **Aggregate** per prior completed ISO week and approved dimensions. Recompute percentages from summed components at each requested rollup. Never average subgroup rates to create a global rate.
6. **Load** via one transaction and idempotent upsert into `reporting.executive_weekly_kpis`. A failed run must not leave a partially published week. Keep run metadata/logs outside `telemetry_events`.
7. **Publish** a run summary and freshness status. The service may return the latest completed aggregate and its coverage statuses; it must not claim real-time availability while sources are batch-only.

## 5. KPI semantics and blocking conditions

The exact output metrics, units, targets, schedule, dimensions and destination are defined in [`company-BRIEFING.md`](./company-BRIEFING.md). Preserve the M01–M10 identifiers from the telemetry plan. In particular:

- M01/M03/M04 require complete denominator cohorts and explicit maturation/attribution windows.
- M02 requires resolving assignment-versus-start semantics before publication.
- M05 must use trustworthy source watermarks and a documented observation instant.
- M06 requires realized costs and billable weight, not estimated assignment cost.
- M07 requires correlated approval and production times.
- M08 requires business incidents and SLA deadlines; technical error events are not incidents.
- M09 counts positive-to-zero transitions with concurrency/retry deduplication.
- M10 requires a defined B2B survey; predicted health scores are not observed satisfaction.

Until a blocking contract is resolved, emit a status record with null `metric_value` and an explanatory `status_reason`, or omit the aggregate only if consumers explicitly distinguish missing from zero. The chosen table contract favors an explicit blocked row so the executive report can disclose coverage gaps.

## 6. Storage contract and idempotency

Destination: **`reporting.executive_weekly_kpis`**. The table is owned by reporting, not telemetry. Use a dedicated schema and least-privilege role. Pipeline writer permissions should be limited to the reporting product; service read permissions should not permit source-table mutation.

Proposed logical grain and fields are documented in `company-BRIEFING.md`. Enforce a deterministic unique key over week range, metric code, dimensions and definition version. Upsert a whole run atomically; use a transaction/advisory lock or equivalent to prevent concurrent writers for the same week. A `run_id`, source watermarks and `calculated_at` make every result traceable. Corrections/backfills rerun the affected week and upsert the same key. Preserve historical definition versions rather than silently rewriting KPI semantics.

Schema creation, SQL migrations, RLS/grants and retention policy require a separate implementation review. Do not infer the existing Supabase/PostgreSQL deployment schema or credentials from local development configuration.

## 7. Schedule, freshness and backfills

- Weekly publication: Mondays 07:00 `America/Los_Angeles`, covering the previous fully completed ISO week in UTC. Confirm this timezone with the business owner before production.
- Incremental refreshes: optional and source-dependent; use explicit source watermarks and bounded recomputation windows for late-arriving events.
- Backfills: operator-triggered by week range, idempotent, rate-limited, audited, and protected from concurrent writes. Record the reason and source snapshot/watermarks.
- Late updates: reprocess the affected cohort/week and replace its aggregate atomically. Define a source-specific finalization/maturation policy for M01/M03/M04 before calling any period final.

## 8. Quality, evaluation and observability

Use `data/eval/` for synthetic/anonymized fixtures and golden KPI cases. Minimum checks:

- schema, required values, valid enum/status, UTC boundaries and nonnegative durations/counts;
- numerator ≤ denominator for rates, valid rate range, M10 within 0–10, and M06 positive denominator;
- unique aggregate key and idempotency under repeated runs;
- reconciliation of totals to source cohorts and numerator/denominator rollups;
- deterministic transformation tests for empty input, late records, duplicate IDs, invalid joins, open/unresolved cohorts, timezone/DST boundaries, and blocked metrics;
- no PII in logs or output dimensions;
- report freshness and source coverage visible per run.

Track operational measures separately from business KPIs: run success/failure, duration, rows read/rejected/written, source lag and retry count. These may be emitted to the existing observability/telemetry system according to its schema, but report values remain in `reporting.executive_weekly_kpis`.

## 9. Failure handling and security

- Retry transient source/network errors with bounded exponential backoff; do not retry deterministic validation errors indefinitely.
- Fail closed on unknown schema versions, incomplete required denominators, missing currency conversion or ambiguous mappings. Publish explicit blocked/partial statuses only under the agreed output contract.
- Stage/validate all rows before transactional publication. On failure, leave the previous successful report intact and mark the run failed in operational run metadata/logging.
- Restrict raw extracts, use opaque IDs, redact credentials and PII, and apply service-level authorization to any customer-level result. Do not expose raw events through reporting endpoints.
- Never fabricate sample values as production metrics; synthetic fixtures must be clearly labeled.

## 10. Reporting service interface (planned)

`services/reporting/` owns the HTTP boundary and may import the pipeline's public entry point. Proposed endpoints, to be finalized when the service is implemented:

- `GET /reporting/executive/weekly?week_start=YYYY-MM-DD` — read a completed week, returning period, generation time, metrics, units, dimensions and coverage status.
- `POST /reporting/executive/weekly/refresh` — controlled/manual refresh for authorized operators; validate week bounds and make invocation idempotent. Do not expose unrestricted arbitrary pipeline execution publicly.

These routes are distinct from `GET /telemetry/report`; they read/report business aggregates and do not recalculate technical telemetry metrics. Return null for blocked metric values and include status/reason. The exact API deployment/integration with the existing FastAPI application, authorization, response cache and refresh permissions must be reviewed before implementation.

## 11. Implementation sequence

1. Confirm source owners, source systems and the contract gaps listed in `company-BRIEFING.md`/telemetry-plan §2.1.
2. Add schema/migration and least-privilege roles for `reporting.executive_weekly_kpis`.
3. Implement one transform per KPI under `data/process/reporting/`, with typed inputs and golden tests; initially publish explicit blocked states for unavailable source contracts.
4. Add extraction, validation, orchestration, atomic upsert, run metadata and backfill controls under `data/pipelines/executive_report/`.
5. Add the separate `services/reporting/` API module, wire it to pipeline/read interfaces, and test dependency direction (no import from pipeline/process to services).
6. Validate against anonymized source snapshots, reconcile with business owners, and only then enable the Monday production schedule and threshold alerts.

## 12. Decisions still requiring owner sign-off

- Monday 07:00 timezone and whether the report is an ISO week in UTC or business-local week.
- Source systems of record, connectors, ownership and update cadence for each KPI.
- M02 start event, cohort maturity for M01/M03/M04, M06 currency and realized-cost policy, M08 incident SLA policy, M09 stock aggregation scope, M10 survey design.
- Country/warehouse/carrier/customer access policy and retention of aggregates.
- Scheduler, deployment topology, migration/grants strategy, API authentication/authorization and alert delivery channels.
