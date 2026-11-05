"""Pure Pandas metrics for technical and operational telemetry events."""

from __future__ import annotations

import pandas as pd


LATENCY_EVENT = "api_latency_recorded"
ERROR_EVENTS = ("frontend_error_recorded", "api_error_breached")
AUTH_FAILURE_EVENT = "login_failed"
AUTH_SUCCESS_EVENT = "login_succeeded"


def _period_frame(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Select events in the explicitly supplied UTC period, inclusive."""
    if not isinstance(events, pd.DataFrame):
        raise TypeError("events must be a pandas DataFrame")
    required = {"timestamp", "event_type", "properties"}
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"events is missing required columns: {', '.join(sorted(missing))}")
    if events.empty:
        return events.copy()

    timestamps = pd.to_datetime(events["timestamp"], utc=True, errors="coerce")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    return events.loc[timestamps.between(start, end, inclusive="both")].copy()


def _properties_frame(events: pd.DataFrame) -> pd.DataFrame:
    """Flatten catalog event properties without modifying the input frame."""
    if not isinstance(events, pd.DataFrame):
        raise TypeError("events must be a pandas DataFrame")
    required = {"event_type", "properties"}
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"events is missing required columns: {', '.join(sorted(missing))}")

    properties = pd.json_normalize(events["properties"].where(events["properties"].notna(), {}).tolist())
    properties.index = events.index
    return pd.concat([events[["event_type"]], properties], axis=1)


def _ensure_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Add absent catalog columns so empty or sparse inputs aggregate safely."""
    return frame.reindex(columns=frame.columns.union(columns, sort=False))


def latency_by_endpoint(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Summarize API latency by service, normalized endpoint, and HTTP method.

    The input rows must use the event envelope's ``event_type`` and ``properties``
    columns; API latency properties follow the ``api_latency_recorded`` catalog.
    """
    frame = _properties_frame(_period_frame(events, start_date, end_date))
    frame = _ensure_columns(frame, ["serviceName", "endpoint", "httpMethod", "latencyMs"])
    latency = frame.loc[
        frame["event_type"].eq(LATENCY_EVENT),
        ["serviceName", "endpoint", "httpMethod", "latencyMs"],
    ].copy()
    latency["latencyMs"] = pd.to_numeric(latency["latencyMs"], errors="coerce")
    latency = latency.loc[latency["latencyMs"].ge(0)]
    return (
        latency.groupby(["serviceName", "endpoint", "httpMethod"], dropna=False)
        .agg(request_count=("latencyMs", "count"), mean_latency_ms=("latencyMs", "mean"))
        .reset_index()
        .sort_values(["serviceName", "endpoint", "httpMethod"], kind="stable", na_position="last")
        .reset_index(drop=True)
    )


def errors_by_category(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Count technical error events by type and catalog error category."""
    frame = _properties_frame(_period_frame(events, start_date, end_date))
    frame = _ensure_columns(frame, ["errorCategory"])
    errors = frame.loc[
        frame["event_type"].isin(ERROR_EVENTS),
        ["event_type", "errorCategory"],
    ].copy()
    errors["errorCategory"] = errors["errorCategory"].fillna("unknown")
    return (
        errors.groupby(["event_type", "errorCategory"], dropna=False)
        .agg(error_count=("event_type", "count"))
        .reset_index()
        .sort_values(["event_type", "errorCategory"], kind="stable")
        .reset_index(drop=True)
    )


def http_status_summary(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Count API latency samples by HTTP status and summarize their latency."""
    frame = _properties_frame(_period_frame(events, start_date, end_date))
    frame = _ensure_columns(frame, ["statusCode", "latencyMs"])
    responses = frame.loc[
        frame["event_type"].eq(LATENCY_EVENT), ["statusCode", "latencyMs"]
    ].copy()
    responses["statusCode"] = pd.to_numeric(responses["statusCode"], errors="coerce")
    responses["latencyMs"] = pd.to_numeric(responses["latencyMs"], errors="coerce")
    responses = responses.loc[responses["statusCode"].notna()]
    summary = (
        responses.groupby("statusCode", dropna=False)
        .agg(
            response_count=("statusCode", "count"),
            mean_latency_ms=("latencyMs", "mean"),
        )
        .reset_index()
        .sort_values("statusCode", kind="stable")
        .reset_index(drop=True)
    )
    summary["error_count"] = summary["response_count"].where(summary["statusCode"].ge(400), 0)
    return summary


def events_per_day(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Count catalog events per UTC calendar day within an explicit period."""
    period = _period_frame(events, start_date, end_date)
    timestamps = pd.to_datetime(period["timestamp"], utc=True, errors="coerce")
    daily = pd.DataFrame({"day": timestamps.dt.strftime("%Y-%m-%d"), "event_type": period["event_type"]})
    daily = daily.dropna(subset=["day"])
    return (
        daily.groupby("day")
        .agg(event_count=("event_type", "count"))
        .reset_index()
        .sort_values("day", kind="stable")
        .reset_index(drop=True)
    )


def error_rate_by_type(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Summarize error-event share by technical error type.

    ``error_rate`` is the percentage of all captured telemetry events in the
    requested period that belong to each supported error event type; it is not
    an HTTP request failure rate because frontend error events lack a request
    denominator in the event catalog.
    """
    period = _period_frame(events, start_date, end_date)
    error_counts = (
        period.loc[period["event_type"].isin(ERROR_EVENTS)]
        .groupby("event_type")
        .agg(error_count=("event_type", "count"))
    )
    error_counts["total_events"] = period["event_type"].count()
    error_counts["error_rate"] = error_counts["error_count"].div(
        error_counts["total_events"].where(error_counts["total_events"].ne(0))
    ).mul(100)
    return (
        error_counts.rename_axis("error_type")
        .reset_index()
        .sort_values("error_type", kind="stable")
        .reset_index(drop=True)
    )


def auth_failure_rate(
    events: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp
) -> pd.DataFrame:
    """Calculate daily failed-login attempts divided by all login attempts.

    The event names follow the repository's telemetry catalog (``login_failed``
    and ``login_succeeded``). Days without any recorded login attempts are not
    included because their rate is undefined.
    """
    period = _period_frame(events, start_date, end_date)
    auth_events = period.loc[
        period["event_type"].isin((AUTH_FAILURE_EVENT, AUTH_SUCCESS_EVENT))
    ].copy()
    auth_events["day"] = pd.to_datetime(
        auth_events["timestamp"], utc=True, errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    auth_events = auth_events.dropna(subset=["day"])
    auth_events["failed_attempt"] = auth_events["event_type"].eq(AUTH_FAILURE_EVENT)
    return (
        auth_events.groupby("day")
        .agg(
            failed_attempts=("failed_attempt", "sum"),
            total_attempts=("event_type", "count"),
        )
        .assign(
            failure_rate=lambda frame: frame["failed_attempts"].div(frame["total_attempts"])
        )
        .reset_index()
        .sort_values("day", kind="stable")
        .reset_index(drop=True)
    )
