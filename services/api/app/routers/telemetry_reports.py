"""Read-only telemetry reporting endpoint backed by Supabase REST."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from urllib.parse import urlencode

import httpx
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services.response_cache import get_or_set

# In the monorepo, the metrics pipeline is a sibling of ``api``. The Docker
# image copies it under /app/services/telemetry, so resolve either layout.
_METRICS_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "services" / "telemetry" / "analysis.py").is_file()
    ),
    None,
)
if _METRICS_ROOT is not None and str(_METRICS_ROOT) not in sys.path:
    sys.path.insert(0, str(_METRICS_ROOT))

from services.telemetry.analysis import auth_failure_rate, error_rate_by_type, events_per_day

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
_PAGE_SIZE = 1000
_MAX_EVENTS = 10000
_DEFAULT_PERIOD = timedelta(days=7)
_MAX_PERIOD = timedelta(days=31)


def _fetch_events(
    start: datetime,
    end: datetime,
    *,
    event_types: tuple[str, ...] | None = None,
) -> list[dict]:
    """Fetch a bounded timestamp range from Supabase using REST pagination."""
    if not settings.supabase_service_role_key:
        raise HTTPException(status_code=503, detail="Telemetry storage is not configured")

    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    query_params = {
        "select": "timestamp,event_type,properties,tags",
        "and": f"(timestamp.gte.{start.isoformat()},timestamp.lte.{end.isoformat()})",
        "order": "timestamp.asc",
    }
    if event_types:
        query_params["event_type"] = f"in.({','.join(event_types)})"
    query = urlencode(query_params)
    url = f"{settings.supabase_telemetry_url}?{query}"
    events: list[dict] = []
    offset = 0

    try:
        while True:
            response = httpx.get(
                url,
                headers={**headers, "Range": f"{offset}-{offset + _PAGE_SIZE - 1}"},
                timeout=15.0,
            )
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise ValueError("Supabase REST response was not an array")
            events.extend(page)
            if len(events) > _MAX_EVENTS:
                raise HTTPException(
                    status_code=422,
                    detail="Report range contains too many events; narrow the period",
                )
            if len(page) < _PAGE_SIZE:
                return events
            offset += _PAGE_SIZE
    except HTTPException:
        raise
    except (httpx.HTTPError, TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Telemetry storage request failed",
        ) from None


@router.get("/report", summary="Reporte técnico-operacional de telemetría")
def telemetry_report(
    start_date: datetime | None = Query(None, description="Inicio inclusivo (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Fin inclusivo (ISO 8601)"),
) -> dict:
    """Return cached daily volume and technical error-rate metrics."""
    requested_start_date = start_date
    requested_end_date = end_date
    now = datetime.now(timezone.utc)
    end = end_date or now
    start = start_date or (end - _DEFAULT_PERIOD)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    else:
        start = start.astimezone(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    else:
        end = end.astimezone(timezone.utc)
    if end < start:
        raise HTTPException(status_code=422, detail="end_date must be after start_date")
    if end - start > _MAX_PERIOD:
        raise HTTPException(status_code=422, detail="Report period cannot exceed 31 days")
    start_date, end_date = start, end

    cache_start = requested_start_date.isoformat() if requested_start_date is not None else "default-start"
    cache_end = requested_end_date.isoformat() if requested_end_date is not None else "default-end"
    cache_key = f"telemetry-report:{settings.supabase_telemetry_url}:{cache_start}:{cache_end}"
    report = get_or_set(
        cache_key,
        lambda: _build_metrics_report(start_date, end_date),
        ttl_seconds=60.0,
    )
    return report


def _build_metrics_report(start_date: datetime, end_date: datetime) -> dict:
    """Fetch events and run each Pandas metric with the resolved period."""
    event_frame = pd.DataFrame(_fetch_events(start_date, end_date))
    if event_frame.empty and not {"timestamp", "event_type", "properties"}.issubset(event_frame.columns):
        event_frame = pd.DataFrame(columns=["timestamp", "event_type", "properties"])
    auth_events = _fetch_events(
        start_date,
        end_date,
        event_types=("login_failed", "login_succeeded"),
    )
    auth_frame = pd.DataFrame(auth_events)
    if auth_frame.empty and not {"timestamp", "event_type", "properties"}.issubset(auth_frame.columns):
        auth_frame = pd.DataFrame(columns=["timestamp", "event_type", "properties"])
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    return {
        "period": {"from": start_date.isoformat(), "to": end_date.isoformat()},
        "metrics": {
            "events_per_day": events_per_day(event_frame, start, end).to_dict("records"),
            "error_rate_by_type": error_rate_by_type(event_frame, start, end).to_dict("records"),
            "auth_failure_rate": auth_failure_rate(auth_frame, start, end).to_dict("records"),
        },
    }
