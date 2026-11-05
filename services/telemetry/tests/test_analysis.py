import pandas as pd
import pandas.testing as pdt
import pytest

from services.telemetry.analysis import (
    auth_failure_rate,
    error_rate_by_type,
    errors_by_category,
    events_per_day,
    http_status_summary,
    latency_by_endpoint,
)


@pytest.fixture
def events():
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-11-05T00:00:00Z",
                "event_type": "api_latency_recorded",
                "properties": {
                    "serviceName": "inventory-api",
                    "endpoint": "/api/v1/inventory/stock",
                    "httpMethod": "GET",
                    "latencyMs": 100,
                    "statusCode": 200,
                },
            },
            {
                "timestamp": "2026-11-05T01:00:00Z",
                "event_type": "api_latency_recorded",
                "properties": {
                    "serviceName": "inventory-api",
                    "endpoint": "/api/v1/inventory/stock",
                    "httpMethod": "GET",
                    "latencyMs": 300,
                    "statusCode": 500,
                },
            },
            {
                "timestamp": "2026-11-05T02:00:00Z",
                "event_type": "api_latency_recorded",
                "properties": {
                    "serviceName": "orders-api",
                    "endpoint": "/api/v1/orders",
                    "httpMethod": "POST",
                    "latencyMs": 50,
                    "statusCode": 201,
                },
            },
            {
                "timestamp": "2026-11-05T03:00:00Z",
                "event_type": "frontend_error_recorded",
                "properties": {"errorCategory": "api_http_error"},
            },
            {
                "timestamp": "2026-11-05T04:00:00Z",
                "event_type": "frontend_error_recorded",
                "properties": {"errorCategory": "api_http_error"},
            },
            {
                "timestamp": "2026-11-05T05:00:00Z",
                "event_type": "api_error_breached",
                "properties": {"errorCategory": "upstream_unavailable"},
            },
            {
                "timestamp": "2026-11-05T06:00:00Z",
                "event_type": "shipment_delivered",
                "properties": {"statusCode": 200, "latencyMs": 1},
            },
        ]
    )


def test_latency_by_endpoint_aggregates_catalog_metrics_and_is_deterministic(events):
    original = events.copy(deep=True)
    start = pd.Timestamp("2026-11-05T00:00:00Z")
    end = pd.Timestamp("2026-11-06T00:00:00Z")
    actual = latency_by_endpoint(events, start, end)
    expected = pd.DataFrame(
        [
            {
                "serviceName": "inventory-api",
                "endpoint": "/api/v1/inventory/stock",
                "httpMethod": "GET",
                "request_count": 2,
                "mean_latency_ms": 200.0,
            },
            {
                "serviceName": "orders-api",
                "endpoint": "/api/v1/orders",
                "httpMethod": "POST",
                "request_count": 1,
                "mean_latency_ms": 50.0,
            },
        ]
    )

    pdt.assert_frame_equal(actual, expected)
    pdt.assert_frame_equal(latency_by_endpoint(events, start, end), actual)
    pdt.assert_frame_equal(events, original)


def test_errors_by_category_counts_technical_errors_only(events):
    actual = errors_by_category(
        events, pd.Timestamp("2026-11-05T00:00:00Z"), pd.Timestamp("2026-11-06T00:00:00Z")
    )
    assert actual.to_dict("records") == [
        {"event_type": "api_error_breached", "errorCategory": "upstream_unavailable", "error_count": 1},
        {"event_type": "frontend_error_recorded", "errorCategory": "api_http_error", "error_count": 2},
    ]


def test_http_status_summary_counts_responses_and_http_errors(events):
    actual = http_status_summary(
        events, pd.Timestamp("2026-11-05T00:00:00Z"), pd.Timestamp("2026-11-06T00:00:00Z")
    )
    assert actual.to_dict("records") == [
        {"statusCode": 200, "response_count": 1, "mean_latency_ms": 100.0, "error_count": 0},
        {"statusCode": 201, "response_count": 1, "mean_latency_ms": 50.0, "error_count": 0},
        {"statusCode": 500, "response_count": 1, "mean_latency_ms": 300.0, "error_count": 1},
    ]


def test_metrics_return_empty_frames_for_empty_input():
    empty_events = pd.DataFrame(columns=["timestamp", "event_type", "properties"])
    start = pd.Timestamp("2026-11-05T00:00:00Z")
    end = pd.Timestamp("2026-11-06T00:00:00Z")
    assert latency_by_endpoint(empty_events, start, end).empty
    assert errors_by_category(empty_events, start, end).empty
    assert http_status_summary(empty_events, start, end).empty


def test_metrics_validate_input_schema():
    with pytest.raises(ValueError, match="event_type"):
        latency_by_endpoint(
            pd.DataFrame({"properties": []}),
            pd.Timestamp("2026-11-05T00:00:00Z"),
            pd.Timestamp("2026-11-06T00:00:00Z"),
        )


def test_period_metrics_filter_events_using_explicit_utc_bounds(events):
    timestamped = events.copy()
    start = pd.Timestamp("2026-11-05T01:00:00Z")
    end = pd.Timestamp("2026-11-05T05:00:00Z")

    assert events_per_day(timestamped, start, end).to_dict("records") == [
        {"day": "2026-11-05", "event_count": 5}
    ]
    assert error_rate_by_type(timestamped, start, end).to_dict("records") == [
        {
            "error_type": "api_error_breached",
            "error_count": 1,
            "total_events": 5,
            "error_rate": 20.0,
        },
        {
            "error_type": "frontend_error_recorded",
            "error_count": 2,
            "total_events": 5,
            "error_rate": 40.0,
        }
    ]


def test_auth_failure_rate_counts_daily_failed_and_successful_attempts():
    auth_events = pd.DataFrame(
        [
            {"timestamp": "2026-11-05T08:00:00Z", "event_type": "login_failed", "properties": {}},
            {"timestamp": "2026-11-05T09:00:00Z", "event_type": "login_succeeded", "properties": {}},
            {"timestamp": "2026-11-05T10:00:00Z", "event_type": "login_failed", "properties": {}},
            {"timestamp": "2026-11-06T08:00:00Z", "event_type": "login_succeeded", "properties": {}},
            {"timestamp": "2026-11-06T09:00:00Z", "event_type": "login_succeeded", "properties": {}},
        ]
    )
    actual = auth_failure_rate(
        auth_events,
        pd.Timestamp("2026-11-05T00:00:00Z"),
        pd.Timestamp("2026-11-06T23:59:59Z"),
    )

    assert actual.to_dict("records") == [
        {"day": "2026-11-05", "failed_attempts": 2, "total_attempts": 3, "failure_rate": 2 / 3},
        {"day": "2026-11-06", "failed_attempts": 0, "total_attempts": 2, "failure_rate": 0.0},
    ]
