"""Prefect entrypoint for TrackFlow's weekly executive reporting pipeline.

The extraction contract is intentionally read-only. In the absence of an
approved shipment-source connector, M01 is explicitly published as blocked;
telemetry delivery events are never treated as the eligible-shipment universe.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from prefect import flow, get_run_logger, task
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from data.process.reporting.m01 import calculate_m01

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "executive_reporting"
EVAL_DIR = PROJECT_ROOT / "data" / "eval" / "executive_reporting"
DEFAULT_TELEMETRY_URL = (
    "https://stkmiwhfkrfksraszovd.supabase.co/rest/v1/telemetry_events"
)


class PipelineConfigurationError(RuntimeError):
    """Raised for missing or unsafe runtime configuration."""


class PipelineValidationError(RuntimeError):
    """Raised when source rows violate the agreed schema contract."""


def _iso_week_bounds(week_start: date) -> tuple[datetime, datetime, date]:
    if week_start.weekday() != 0:
        raise ValueError("week_start must be a Monday (UTC ISO-week boundary)")
    week_end = week_start + timedelta(days=7)
    return (
        datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc),
        datetime.combine(week_end, datetime.min.time(), tzinfo=timezone.utc),
        week_end,
    )


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise PipelineValidationError("Source timestamp has an unsupported type")
    if parsed.tzinfo is None:
        raise PipelineValidationError("Source timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _get_read_engine() -> Engine:
    """Create a source DB engine using read-only credentials only."""
    source_url = os.getenv("REPORTING_SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not source_url:
        raise PipelineConfigurationError(
            "Set REPORTING_SOURCE_DATABASE_URL to an approved read-only source URL"
        )
    if source_url.startswith("sqlite"):
        # SQLite remains useful for isolated test fixtures; production source
        # access is expected to be PostgreSQL/Supabase using a read-only role.
        return create_engine(source_url)
    if not source_url.startswith(("postgresql://", "postgresql+")):
        raise PipelineConfigurationError("Source URL must use PostgreSQL")
    return create_engine(source_url, pool_pre_ping=True)


def _get_destination_engine() -> Engine:
    """Create a separate reporting writer engine, never a telemetry writer."""
    destination_url = os.getenv("REPORTING_DATABASE_URL")
    if not destination_url:
        raise PipelineConfigurationError(
            "Set REPORTING_DATABASE_URL for the reporting destination"
        )
    if not destination_url.startswith(("postgresql://", "postgresql+")):
        raise PipelineConfigurationError(
            "REPORTING_DATABASE_URL must use PostgreSQL"
        )
    return create_engine(destination_url, pool_pre_ping=True)


def _fetch_telemetry_events(
    *,
    week_start: date,
    source_engine: Engine | None = None,
    telemetry_url: str | None = None,
    api_key: str | None = None,
) -> tuple[list[dict[str, Any]], datetime | None]:
    """Read only M01 delivery events; choose direct DB or Supabase REST source."""
    start, end, _ = _iso_week_bounds(week_start)
    if source_engine is not None:
        with source_engine.connect() as connection:
            with connection.begin():
                if source_engine.dialect.name == "postgresql":
                    connection.execute(text("SET TRANSACTION READ ONLY"))
                result = connection.execute(
                    text(
                        """
                        SELECT event_id, timestamp, event_type, schema_version,
                               properties, received_at
                        FROM telemetry_events
                        WHERE event_type = :event_type
                          AND received_at >= :start_at AND received_at < :end_at
                        ORDER BY received_at, event_id
                        """
                    ),
                    {
                        "event_type": "shipment_delivered",
                        "start_at": start,
                        "end_at": end,
                    },
                ).mappings()
                records = [dict(row) for row in result]
        watermark = max(
            (_parse_datetime(row.get("received_at")) for row in records),
            default=None,
        )
        return records, watermark

    telemetry_url = telemetry_url or os.getenv(
        "TELEMETRY_EVENTS_URL", DEFAULT_TELEMETRY_URL
    )
    # Use a dedicated read-only credential. Never fall back to a service-role
    # key that can mutate telemetry_events.
    api_key = api_key or os.getenv("SUPABASE_REPORTING_READONLY_KEY")
    if not api_key:
        # Do not fabricate telemetry. An absent credential can still produce a
        # blocked M01 snapshot, recorded distinctly by the caller.
        return [], None

    headers = {"apikey": api_key, "Authorization": f"Bearer {api_key}"}
    if not telemetry_url.startswith("https://"):
        raise PipelineConfigurationError("Telemetry REST endpoint must use HTTPS")
    all_records: list[dict[str, Any]] = []
    offset = 0
    page_size = 1000
    while True:
        response = httpx.get(
            telemetry_url,
            params=[
                ("select", "event_id,timestamp,event_type,schema_version,properties,received_at"),
                ("event_type", "eq.shipment_delivered"),
                ("received_at", f"gte.{start.isoformat()}"),
                ("received_at", f"lt.{end.isoformat()}"),
                ("order", "received_at.asc,event_id.asc"),
                ("limit", str(page_size)),
                ("offset", str(offset)),
            ],
            headers={**headers, "Range-Unit": "items", "Range": f"{offset}-{offset + page_size - 1}"},
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not isinstance(batch, list):
            raise PipelineValidationError("Telemetry response must be a list")
        all_records.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    # PostgREST gte is supported; cap to the ISO week in the client to enforce
    # the exclusive UTC end boundary without mutating source data.
    records = [
        record
        for record in all_records
        if (received := _parse_datetime(record.get("received_at"))) is not None
        and start <= received < end
    ]
    watermark = max(
        (_parse_datetime(record.get("received_at")) for record in records),
        default=None,
    )
    return records, watermark


def _event_properties(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate envelope identifiers and the telemetry schema allowlist."""
    registry_path = PROJECT_ROOT / "docs" / "telemetry" / "event-schemas.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    schema = registry["event_schemas"]["shipment_delivered"]
    allowed = set(schema["allowlist"])
    required = set(schema.get("required", []))
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.get("event_type") != "shipment_delivered":
            raise PipelineValidationError("Unexpected event_type in telemetry extract")
        if str(record.get("schema_version")) != "1.0":
            raise PipelineValidationError("Unknown shipment_delivered schema version")
        event_id = record.get("event_id")
        if not event_id:
            raise PipelineValidationError("Telemetry row is missing event_id")
        props = record.get("properties")
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except json.JSONDecodeError as exc:
                raise PipelineValidationError("Telemetry properties are invalid JSON") from exc
        if not isinstance(props, Mapping):
            raise PipelineValidationError("Telemetry properties must be an object")
        if set(props) - allowed or required - set(props):
            raise PipelineValidationError("Telemetry properties violate the allowlist")
        deduped[str(event_id)] = dict(props)
    return list(deduped.values())


def _fetch_authoritative_shipments(
    *,
    week_start: date,
    source_engine: Engine | None,
) -> tuple[list[dict[str, Any]] | None, bool, datetime | None]:
    """Read the approved shipment projection; currently disabled by default.

    The TrackFlow repository does not yet define the authoritative shipment
    cohort table/schema. Enabling this query requires owner-approved identifiers,
    statuses, exclusions and a completeness watermark contract.
    """
    table = os.getenv("REPORTING_SHIPMENTS_TABLE")
    if not table:
        return None, False, None
    # Merely naming a table must not certify that it is the complete cohort.
    # The owner must explicitly approve both the source contract and its
    # completeness guarantee before M01 can use it as a denominator.
    if os.getenv("REPORTING_SHIPMENTS_SOURCE_APPROVED") != "true":
        raise PipelineConfigurationError(
            "Shipment source requires explicit owner approval"
        )
    if os.getenv("REPORTING_SHIPMENTS_COHORT_COMPLETE") != "true":
        return None, False, None
    if source_engine is None:
        raise PipelineConfigurationError(
            "Shipment table requires a configured PostgreSQL source database"
        )
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?", table):
        raise PipelineConfigurationError("Unsafe shipment table identifier")
    start, end, _ = _iso_week_bounds(week_start)
    # Required owner-approved table projection: shipment_id, cohort_created_at,
    # country, eligible, promised_date, delivered_at, source_updated_at.
    query = text(
        f"""SELECT shipment_id, cohort_created_at, country, eligible,
                   promised_date, delivered_at, source_updated_at
            FROM {table}
            WHERE cohort_created_at >= :start_at AND cohort_created_at < :end_at
            ORDER BY cohort_created_at, shipment_id"""
    )
    with source_engine.connect() as connection:
        with connection.begin():
            if source_engine.dialect.name == "postgresql":
                connection.execute(text("SET TRANSACTION READ ONLY"))
            result = connection.execute(
                query, {"start_at": start, "end_at": end}
            ).mappings()
            rows = [dict(row) for row in result]
    watermark = max(
        (_parse_datetime(row.get("source_updated_at")) for row in rows),
        default=None,
    )
    return rows, True, watermark


@task(name="extract_sources_task", retries=2, retry_delay_seconds=[1, 3])
def extract_sources_task(week_start: date) -> dict[str, Any]:
    """Read `telemetry_events` and, only if configured, shipment source read-only."""
    logger = get_run_logger()
    start, end, week_end = _iso_week_bounds(week_start)
    source_engine: Engine | None = None
    if os.getenv("REPORTING_SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL"):
        source_engine = _get_read_engine()
    try:
        events, telemetry_watermark = _fetch_telemetry_events(
            week_start=week_start, source_engine=source_engine
        )
        shipments, cohort_complete, shipment_watermark = _fetch_authoritative_shipments(
            week_start=week_start, source_engine=source_engine
        )
        properties = _event_properties(events)
    except (httpx.HTTPError, OperationalError) as exc:
        # Limited task retries handle transient errors; no exception text/payload
        # is logged because source URLs may include credentials.
        logger.warning("Source extract temporarily unavailable (%s)", type(exc).__name__)
        raise
    finally:
        if source_engine is not None:
            source_engine.dispose()

    RAW_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if RAW_DIR.is_symlink():
        raise PipelineConfigurationError("Raw staging directory must not be a symlink")
    staging_path = RAW_DIR / f"{week_start.isoformat()}-staging.json"
    # Protected local staging contains opaque shipment IDs and source fields.
    # Restrict file permissions and never commit generated extracts.
    os.chmod(RAW_DIR, 0o700)
    temporary_path = staging_path.with_suffix(".json.tmp")
    file_descriptor = os.open(
        temporary_path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as staging_file:
        json.dump(
            {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                # Store only the allowlisted event properties needed by M01;
                # never persist session/user/request identifiers in local staging.
                "delivery_properties": properties,
                "shipments": shipments,
                "cohort_complete": cohort_complete,
                "telemetry_watermark": telemetry_watermark.isoformat()
                if telemetry_watermark
                else None,
                "shipment_watermark": shipment_watermark.isoformat()
                if shipment_watermark
                else None,
            },
            staging_file,
            default=str,
        )
        staging_file.flush()
        os.fsync(staging_file.fileno())
    os.replace(temporary_path, staging_path)
    logger.info(
        "Extracted source rows for M01: telemetry=%d shipments=%d cohort_complete=%s",
        len(events),
        len(shipments or []),
        cohort_complete,
    )
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "staging_path": str(staging_path),
        "telemetry_count": len(events),
        "shipment_count": len(shipments or []),
        "cohort_complete": cohort_complete,
        "source_watermarks": {
            "telemetry_events": telemetry_watermark.isoformat()
            if telemetry_watermark
            else None,
            "shipments": shipment_watermark.isoformat()
            if shipment_watermark
            else None,
        },
        "source_watermark": max(
            [w for w in (telemetry_watermark, shipment_watermark) if w], default=None
        ).isoformat()
        if telemetry_watermark or shipment_watermark
        else None,
    }


@task(name="transform_validate_m01_task")
def transform_validate_m01_task(
    extraction: dict[str, Any], run_id: str
) -> dict[str, Any]:
    """Transform validated TrackFlow shipment cohort and delivery telemetry to M01."""
    staging_path = Path(extraction["staging_path"])
    if (
        staging_path.parent != RAW_DIR
        or staging_path.is_symlink()
        or not staging_path.is_file()
    ):
        raise PipelineValidationError("Expected protected staging file is unavailable")
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    week_start = date.fromisoformat(staging["week_start"])
    properties = staging.get("delivery_properties", [])
    result = calculate_m01(
        week_start=week_start,
        shipments=staging.get("shipments"),
        delivery_events=properties,
        cohort_complete=bool(staging.get("cohort_complete")),
        source_watermark=(
            _parse_datetime(extraction["source_watermark"])
            if extraction.get("source_watermark")
            else None
        ),
        run_id=run_id,
    )
    return {
        "week_start": result.week_start.isoformat(),
        "week_end": result.week_end.isoformat(),
        "status": result.status,
        "status_reason": result.status_reason,
        "rows": [
            {
                **row,
                "week_start": row["week_start"].isoformat(),
                "week_end": row["week_end"].isoformat(),
                "source_watermark": row["source_watermark"].isoformat()
                if row["source_watermark"]
                else None,
                "calculated_at": row["calculated_at"].isoformat(),
            }
            for row in result.metric_rows
        ],
        "source_watermark": extraction.get("source_watermark"),
    }


def _ensure_reporting_table(connection: Any) -> None:
    """Assert the reviewed destination exists; runtime DDL is forbidden."""
    result = connection.execute(
        text("SELECT to_regclass('reporting.executive_weekly_kpis')")
    ).scalar_one()
    if result is None:
        raise PipelineConfigurationError(
            "Create reporting.executive_weekly_kpis through the reviewed migration before running the pipeline"
        )


def _create_optional_eval_snapshot(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Write sanitized, aggregate-only evaluation output; no source payloads."""
    if not rows:
        raise PipelineValidationError("Cannot create an eval snapshot without KPI rows")
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "metrics": [
            {
                "week_start": row["week_start"],
                "week_end": row["week_end"],
                "metric_code": row["metric_code"],
                "metric_value": row["metric_value"],
                "unit": row["unit"],
                "status": row["status"],
                "dimensions": row["dimensions"],
            }
            for row in rows
        ],
    }
    output = EVAL_DIR / f"m01-{snapshot['metrics'][0]['week_start']}-latest.json"
    output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    os.chmod(output, 0o600)
    return {"eval_snapshot": str(output), "row_count": len(rows)}


@task(name="load_weekly_kpis_task", retries=1, retry_delay_seconds=2)
def load_weekly_kpis_task(transformed: dict[str, Any]) -> dict[str, Any]:
    """Atomically upsert M01 rows into reporting.executive_weekly_kpis."""
    engine = _get_destination_engine()
    rows = transformed["rows"]
    if not rows:
        raise PipelineValidationError("Refusing to publish an empty KPI row set")
    statement = text(
        """INSERT INTO reporting.executive_weekly_kpis (
              week_start, week_end, metric_code, metric_name, definition_version,
              metric_value, unit, status, status_reason, dimensions, numerator,
              denominator, source_watermark, calculated_at, run_id
            ) VALUES (
              :week_start, :week_end, :metric_code, :metric_name, :definition_version,
              :metric_value, :unit, :status, :status_reason,
              CAST(:dimensions AS jsonb), :numerator, :denominator,
              :source_watermark, :calculated_at, CAST(:run_id AS uuid)
            )
            ON CONFLICT (week_start, week_end, metric_code, dimensions, definition_version)
            DO UPDATE SET metric_name = EXCLUDED.metric_name,
              metric_value = EXCLUDED.metric_value, unit = EXCLUDED.unit,
              status = EXCLUDED.status, status_reason = EXCLUDED.status_reason,
              numerator = EXCLUDED.numerator, denominator = EXCLUDED.denominator,
              source_watermark = EXCLUDED.source_watermark,
              calculated_at = EXCLUDED.calculated_at, run_id = EXCLUDED.run_id"""
    )
    try:
        with engine.begin() as connection:
            _ensure_reporting_table(connection)
            # Per-grain unique constraint plus a transaction makes publication
            # idempotent without out-of-scope locks or destructive cleanup.
            for row in rows:
                payload = dict(row)
                payload["dimensions"] = json.dumps(row["dimensions"], sort_keys=True)
                payload["run_id"] = transformed.get("run_id") or row["run_id"]
                connection.execute(statement, payload)
            # Upserts are idempotent; don't delete other dimensions on a replay.
    finally:
        engine.dispose()
    return {
        "week_start": transformed["week_start"],
        "week_end": transformed["week_end"],
        "metric_rows_written": len(rows),
        "status": transformed["status"],
        "source_watermark": transformed.get("source_watermark"),
    }


@task(name="create_eval_snapshot_task", persist_result=False)
def create_eval_snapshot_task(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Optional non-critical aggregate-only evaluation export."""
    return _create_optional_eval_snapshot(rows)


@flow(name="executive_weekly_report_flow", log_prints=False)
def executive_weekly_report_flow(
    week_start: date,
    trigger_type: str = "manual",
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Extract, validate/transform and publish the weekly TrackFlow M01 report."""
    _iso_week_bounds(week_start)
    if trigger_type not in {"scheduled", "manual", "retry", "backfill"}:
        raise ValueError("Unsupported trigger_type")
    run_id = str(uuid4())
    logger = get_run_logger()
    logger.info("Starting executive weekly reporting run_id=%s", run_id)

    extraction = extract_sources_task(week_start)
    transformed = transform_validate_m01_task(extraction, run_id)
    transformed["run_id"] = run_id
    loaded = load_weekly_kpis_task(transformed)

    # A failed optional snapshot must never turn successful publication into
    # a failed flow. Prefect returns the task's failed state on this call.
    # Call as a Prefect task with return_state=True, so task failures are returned
    # as a state rather than raised into the successful primary flow.
    optional_state = create_eval_snapshot_task(
        transformed["rows"], return_state=True
    )
    if optional_state.is_failed():
        logger.warning("Optional M01 eval snapshot failed; KPI publication succeeded")

    return {
        **loaded,
        "run_id": run_id,
        "trigger_type": trigger_type,
        "idempotency_key": idempotency_key,
        "optional_eval_state": optional_state.name,
    }


@flow(name="executive_report_backfill_flow", log_prints=False)
def executive_report_backfill_flow(
    start_week: date, end_week: date, trigger_type: str = "backfill"
) -> list[dict[str, Any]]:
    """Run a bounded sequence of weekly reports, one ISO week at a time."""
    _iso_week_bounds(start_week)
    _iso_week_bounds(end_week)
    if end_week < start_week:
        raise ValueError("end_week must be on or after start_week")
    results = []
    week = start_week
    while week <= end_week:
        results.append(executive_weekly_report_flow(week, trigger_type=trigger_type))
        week += timedelta(days=7)
    return results


__all__ = [
    "create_eval_snapshot_task",
    "executive_report_backfill_flow",
    "executive_weekly_report_flow",
    "extract_sources_task",
    "load_weekly_kpis_task",
    "transform_validate_m01_task",
]
