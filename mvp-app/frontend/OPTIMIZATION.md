# Frontend optimization notes

## App and routes reviewed

The MVP is a single Next.js App Router page (`/`); there are no separate feature routes to defer. The page's two optional operational tools are the lazy-loading candidates:

1. **`ServiceDiagnostics`** — detailed checks against the UI and API, including response parsing and a user-triggered retry. It is below the primary status summary and is not needed to understand the initial screen. `next/dynamic` therefore keeps its code out of the initial client bundle and loads it when the user opens the diagnostics disclosure.
2. **`HealthHistoryPanel`** — retains up to 1,000 samples and periodically computes availability, average latency, and a sorted p95 latency. It is supplementary observability, not required for initial health status. It loads only after the user opens its disclosure, avoiding its state/polling work for visitors who do not need it.

## Memoization

`HealthHistoryPanel` uses `useMemo` to filter samples, sort latency values, and calculate p95/average/success rate. Sorting is O(n log n), with at most 1,000 samples. The dependency is exactly `[samples]`, the sole source of the summary values; the summary is recomputed only when a new sample is collected.

## API caching assessment

The inventory API is independent of this MVP's `/status` API; endpoint cache analysis and implementation are documented in `services/api/CACHING.md`.
