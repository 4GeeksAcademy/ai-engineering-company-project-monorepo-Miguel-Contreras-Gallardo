# API endpoint inventory and caching assessment

The FastAPI app in `services/api/app/main.py` exposes `/`, `/healthz`, `/api/v1/incidents/*`, `/articles/*`, and `/inventory/*`. Cost/frequency/stability are qualitative estimates for dashboard use; incidents and stock are live operational data, so only aggregates with a short TTL are cached.

| Endpoint(s) | Cost | Expected frequency | Data stability | Decision |
|---|---|---|---|---|
| `GET /`, `GET /healthz` | Trivial | High (probes) | Response constant | No cache needed; computation is negligible and uptime should remain current. |
| `GET /api/v1/incidents` (all filters/pagination) | Medium/high (count + page query and optional text search) | High on incident dashboard | Low; changes on every incident mutation | Not cached: broad filter combinations and freshness outweigh benefit. |
| `GET /api/v1/incidents/{id}` | Low (indexed primary-key lookup) | Medium | Low for active records | Not cached: cheap query, frequently updated. |
| `GET /api/v1/incidents/{id}/audit` | Medium (incident check + ordered event history) | Low/medium | Append-only but changes after every mutation | Not cached: mutability and per-incident keys make short-lived cache less valuable. |
| `GET /api/v1/incidents/stats` | High (four aggregate queries over incidents) | High (dashboard polling/refresh) | Medium/low during operations | Cached 20 seconds; invalidated after incident writes. |
| `GET /api/v1/incidents/open-by-severity` | Medium (grouped aggregate) | High (dashboard widget) | Medium/low during operations | Cached 20 seconds; invalidated after incident writes. |
| `GET /articles/` | Low/medium (ordered catalogue query) | High in backoffice | Medium/high; catalogue changes infrequently | Candidate by stability/frequency, but not cached yet to avoid serving stale data without adding catalogue invalidation complexity. |
| `GET /articles/{sku}` | Low (primary-key lookup) | Medium | Medium/high | Not cached; cheap lookup. |
| `GET /articles/{sku}/lots`, `GET /articles/{sku}/lots/{lot_code}` | Low (indexed lookups) | Medium | Medium; lots added occasionally | Not cached; relatively cheap and write invalidation would be required. |
| `GET /inventory/stock` | Medium (grouped ledger query) | High on inventory dashboard | Low; each movement changes it | Not cached: stock must reflect committed movements immediately. |
| `GET /inventory/reorder` | High (loads catalogue and derives stock for each item) | High on inventory dashboard | Low/medium; changes on movements and article edits | Cached 20 seconds and invalidated after movements. Article create/update/deactivate/lot creation can also affect its input or eligibility; these writes clear it as well. |
| `GET /inventory/movements?request_key=...` | Low/medium (key lookup + stock lookup) | Low (idempotency inspection) | Low; result is derived from a changing ledger | Not cached: resulting stock should be fresh. |

## Implementation notes

- `app/services/response_cache.py` is a thread-safe, process-local TTL cache with defensive copies and per-database-engine key scope (important for isolated tests).
- Cached endpoints: `GET /api/v1/incidents/stats`, `GET /api/v1/incidents/open-by-severity`, and `GET /inventory/reorder`.
- All incident create/update/assign/transition paths invalidate the incident aggregates. Inventory movement and article/lot create/update/deactivate paths invalidate the reorder aggregate.
- The cache is local to one worker and is lost on restart; each worker has its own 20-second TTL. Use shared Redis if deployment requires cross-worker coherence. The TTL bounds staleness if another process writes to the database.
- MVP `mvp-app/backend` currently exposes only `GET /status`; it performs a database connectivity check and should remain uncached because it is a health probe whose purpose is freshness. The inventory/incident API is the FastAPI service that benefits from aggregate caching.