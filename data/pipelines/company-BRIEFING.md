# Company Briefing — Executive Reporting Pipeline

> **Status:** Project-specific working brief, created from the TrackFlow Academy context and the telemetry plan in this repository. KPI definitions with incomplete source coverage are explicitly marked; they must not be presented as measured results until their source contracts are complete.

## Company and business context

TrackFlow is a last-mile logistics and warehouse-management company operating in the United States and Spain, with warehouses in Los Angeles and Zaragoza. It serves e-commerce brands and manages orders, inventory, shipments, carriers, returns, and customer support. This project designs an executive reporting pipeline to replace the manual weekly consolidation described in the Academy briefing (`CONTEXT-trackflow-briefing.md`, `feature/incident-manager`) and `CONTEXT.md`.

The CEO and executive team need a consolidated view of both operations, country comparisons, threshold alerts, and a weekly report. Department owners are secondary consumers of the same governed metrics. This is a reporting data product, not a telemetry-event ingestion feature.

## KPIs a medir

The mandatory metric set is M01–M10 from [`docs/telemetry/telemetry-plan.md`, section 2](../../docs/telemetry/telemetry-plan.md). The telemetry plan also documents important coverage caveats in §2.1; those caveats are part of this contract. The pipeline must not silently infer missing denominators or call proxies actual outcomes.

| ID | KPI and output | Definition / aggregation | Output unit | Initial data-readiness rule |
|---|---|---|---|---|
| M01 | On-time delivery rate | On-time eligible shipments / all eligible shipments in the same shipment cohort × 100. Report globally and by destination country when a complete shipment cohort exists. | Percent | **Blocked** until the authoritative shipment source supplies the full eligible denominator, promised date, delivery/pending state, cohort and exclusions. `shipment_delivered` alone is not enough. |
| M02 | Average picking time | Mean completed picking duration, using one agreed start-to-completion interval per order. Report globally and by warehouse when IDs and timestamps are trustworthy. | Minutes/order | **Blocked pending definition alignment**: the plan describes assignment-to-completion, while the formal event currently supplies start/completion fields. Do not mix definitions. |
| M03 | Return rate | Returns attributable to an eligible shipment cohort / shipments in that same cohort × 100, after the agreed attribution/maturation window. Report globally and by country where available. | Percent | **Blocked** until a shipment denominator, return-to-shipment join key, attribution window and cohort maturity are available. |
| M04 | Automatic CX resolution rate | Eligible tickets resolved automatically without human intervention within the resolution window / all eligible tickets in the same ticket cohort × 100. | Percent | **Blocked** until the complete ticket universe, eligibility, recontact/reopen and resolution-window rules are sourced. `ticket_auto_resolved` alone is only a numerator. |
| M05 | Executive data freshness | Report/query observation time minus the source watermark for the data included. Publish the maximum source age and per-source freshness so a stale source is visible. | Seconds (plus rendered duration) | **Partial** until every contributing source provides a reliable watermark and the observation-time semantics are fixed. Never substitute event occurrence time for ingestion/source watermark without labeling it. |
| M06 | Shipping cost per kg | Sum of realized, settled shipping cost / sum of billable weight in kg, weighted by totals, grouped by carrier and route/country where available. | Currency/kg | **Blocked** until invoice/settlement cost, currency normalization, billable weight and route are sourced. Estimated carrier-assignment cost must not be labeled realized cost. |
| M07 | Deployment lead time | Production timestamp minus approved timestamp for a correlated change/deployment. | Duration (minutes or hours) | **Blocked** until approval and production timestamps are correlated and rollback/failed-deployment treatment is defined. Deployment duration alone is not lead time. |
| M08 | Incidents resolved within SLA | Incidents resolved on or before SLA deadline / all incidents whose SLA deadline falls in the reporting cohort × 100; unresolved incidents after deadline count as breaches. | Percent | **Blocked** until incident creation, resolution, deadline, eligibility and reopen semantics are sourced. Technical errors/latency events are not business incidents. |
| M09 | Stockout transitions | Count transitions from positive available stock to zero, by SKU and warehouse (and client when authoritative ownership is available); deduplicate retries and repeated zero readings. | Count | **Blocked pending reliable SKU/client/warehouse mapping and atomic transition semantics**. A rejected stock edit is not a stockout. |
| M10 | B2B customer satisfaction | Mean valid responses to a defined B2B logistics-satisfaction survey on a 0–10 scale, by customer and period; publish response count/rate. Keep observed survey satisfaction distinct from predictive customer-health/renewal scores. | Score (0–10), response count/rate | **Blocked** until survey instrument, eligible population, response source and client mapping are defined. A health score or CX ticket rating is not automatically equivalent. |

### Shared reporting rules

- **Audience:** CEO and executive leadership first; department owners may consume the same metric definitions and country/warehouse/carrier/customer dimensions subject to authorization.
- **Cadence:** Refresh the reporting product on demand or from source updates as infrastructure allows; publish a consolidated weekly report every Monday at **07:00 America/Los_Angeles** (the headquarters timezone is an explicit project assumption; confirm before production scheduling). The weekly report covers the previous fully completed ISO week, using UTC event timestamps for deterministic boundaries.
- **Aggregation:** Global totals are recomputed from numerators and denominators, never averaged from percentages. Country/carrier/warehouse/customer splits are emitted only where the source supports an unambiguous mapping. The grain and valid dimensions are included with each KPI result.
- **Unavailable values:** Store a null numeric value and a status/reason (`available`, `partial`, `blocked`, or `not_applicable`) rather than zero or a fabricated estimate. Include source watermark and calculation timestamp.
- **Thresholds:** M01 >97%, M02 <15 minutes, M04 >60%, M07 <1 day, M08 >95%, M09 target 0, and M10 >8/10 are initial targets from the telemetry plan/project brief. M03's 18–25% is a reference range, not a quality target. M05 aims for under five minutes in the telemetry plan; M06 has no target. Alerts require complete/valid data and must identify unavailable KPIs instead of treating them as breaches.

## Destination table

Write the executive reporting product to **`reporting.executive_weekly_kpis`** (PostgreSQL schema `reporting`, table `executive_weekly_kpis`). This exact qualified name is the destination contract for this repository's pipeline. Do not write business aggregates to `telemetry_events` and do not substitute a generic `reporting.business_metrics` table.

Suggested row grain: one row per `(week_start, metric_code, dimensions)` combination. Store at least:

- `week_start`, `week_end` — UTC ISO-week boundaries;
- `metric_code`, `metric_name`, `definition_version`;
- `metric_value` nullable numeric, `unit`, `status`, `status_reason`;
- `dimensions` JSONB (only approved, non-PII keys such as country, warehouse, carrier; client dimension only where access controls permit);
- `numerator` / `denominator` where applicable, to support auditability and correct rollups;
- `source_watermark`, `calculated_at`, and pipeline `run_id` for lineage and freshness.

Use a uniqueness/upsert key equivalent to `(week_start, week_end, metric_code, dimensions, definition_version)` so reruns replace the same logical aggregate rather than duplicate it. Final DDL, constraints, grants and row-level access policies are part of implementation and must be reviewed before production.

## Non-goals and safety

- This brief does not assert that all M01–M10 source data is already captured or that every KPI is currently computable.
- This pipeline does not alter the technical `GET /telemetry/report` contract, append calculated reports to `telemetry_events`, or use authentication/operational telemetry as a proxy for business outcomes.
- Do not copy raw PII, addresses, tracking numbers, free text or customer names into aggregate output. Keep any customer-level reporting access-controlled and use opaque IDs.
- `docs/telemetry/telemetry-plan.md` §2.1 remains the source of truth for the current metric-coverage caveats; resolve documented gaps with source owners before promoting a blocked KPI to available.
