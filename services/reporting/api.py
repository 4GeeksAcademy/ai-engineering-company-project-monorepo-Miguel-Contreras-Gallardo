"""HTTP boundary for executive reporting aggregates.

This module is deliberately independent of the FastAPI application package.
The application supplies its database-session dependency when creating the
router; pipeline code is not imported by this read-only API module.
"""

from collections.abc import Callable, Iterator
from datetime import date, datetime
import hmac
import os
import sys
from typing import Any
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# The standalone reporting package and pipeline are siblings in the repository.
# Resolve both monorepo and copied container layouts without coupling to app.*.
_REPOSITORY_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "data" / "pipelines" / "pipeline.py").is_file()
    ),
    None,
)
if _REPOSITORY_ROOT is not None and str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from services.reporting.pipeline_interface import (
    PipelineInterfaceError,
    get_executive_report_status,
    request_executive_weekly_report,
)


class ExecutiveMetric(BaseModel):
    """One persisted KPI aggregate, including its coverage status."""

    model_config = ConfigDict(extra="ignore")

    metric_code: str
    metric_name: str
    definition_version: str
    metric_value: float | None
    unit: str
    status: str
    status_reason: str | None = None
    dimensions: dict[str, Any]
    numerator: float | None = None
    denominator: float | None = None
    source_watermark: datetime | None = None
    calculated_at: datetime
    run_id: str


class ExecutiveWeeklyReport(BaseModel):
    """A weekly snapshot of executive KPIs."""

    week_start: date
    week_end: date
    metrics: list[ExecutiveMetric]


class ExecutiveRunStatus(BaseModel):
    """Latest pipeline run status plus its safe audit metadata."""

    status: str
    run: dict[str, Any] | None


class ExecutiveRunRequest(BaseModel):
    """Manual request to run the weekly TrackFlow M01 reporting flow."""

    week_start: date


class ExecutiveRunResponse(BaseModel):
    """Accepted/completed manual run and idempotency result."""

    status: str
    run: dict[str, Any]
    deduplicated: bool


_SELECT_WEEKLY_REPORT = text(
    """
    SELECT
        week_start,
        week_end,
        metric_code,
        metric_name,
        definition_version,
        metric_value,
        unit,
        status,
        status_reason,
        dimensions,
        numerator,
        denominator,
        source_watermark,
        calculated_at,
        run_id
    FROM reporting.executive_weekly_kpis
    WHERE week_start = COALESCE(
        :week_start,
        (SELECT MAX(week_start) FROM reporting.executive_weekly_kpis)
    )
    ORDER BY metric_code, dimensions::text
    """
)


def create_reporting_router(
    get_db: Callable[..., Iterator[Session]],
) -> APIRouter:
    """Create reporting routes using the host application's DB dependency."""
    router = APIRouter(prefix="/reporting/executive", tags=["reporting"])

    def require_reporting_operator(
        x_reporting_operator_key: str | None = Header(default=None),
    ) -> None:
        """Fail closed unless a configured operator token matches in constant time."""
        expected = os.getenv("REPORTING_OPERATOR_TOKEN")
        if not expected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Manual reporting is not configured",
            )
        if not x_reporting_operator_key or not hmac.compare_digest(
            x_reporting_operator_key, expected
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Reporting operator authentication required",
            )

    @router.get("/status", response_model=ExecutiveRunStatus)
    def get_latest_run_status(
        week_start: date | None = Query(
            default=None,
            description="Optional Monday ISO date to scope the latest run.",
        ),
    ) -> ExecutiveRunStatus:
        """Return the latest run record without triggering a pipeline execution."""
        _validate_week_start(week_start)
        try:
            return ExecutiveRunStatus(**get_executive_report_status(week_start))
        except PipelineInterfaceError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Executive reporting run metadata is unavailable",
            ) from None

    @router.post(
        "/weekly/refresh",
        response_model=ExecutiveRunResponse,
        dependencies=[Depends(require_reporting_operator)],
    )
    def trigger_weekly_report(
        payload: ExecutiveRunRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> ExecutiveRunResponse:
        """Run the named Prefect pipeline flow for one week, operator-only."""
        _validate_week_start(payload.week_start)
        try:
            result = request_executive_weekly_report(
                payload.week_start,
                idempotency_key=idempotency_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        except PipelineInterfaceError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Executive reporting flow is unavailable",
            ) from None
        return ExecutiveRunResponse(**result)

    @router.get("/weekly", response_model=ExecutiveWeeklyReport)
    def get_weekly_report(
        week_start: date | None = Query(
            default=None,
            description="UTC Monday start date; omitted to request the latest week.",
        ),
        db: Session = Depends(get_db),
    ) -> ExecutiveWeeklyReport:
        """Return a persisted weekly report without recalculating business KPIs."""
        _validate_week_start(week_start)

        try:
            rows = db.execute(
                _SELECT_WEEKLY_REPORT,
                {"week_start": week_start},
            ).mappings().all()
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="Executive reporting storage is unavailable",
            ) from None

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No executive weekly report is available for the requested week",
            )

        report_start = rows[0]["week_start"]
        report_end = rows[0]["week_end"]
        if any(row["week_start"] != report_start or row["week_end"] != report_end for row in rows):
            raise HTTPException(
                status_code=503,
                detail="Executive reporting data contains inconsistent week boundaries",
            )

        return ExecutiveWeeklyReport(
            week_start=report_start,
            week_end=report_end,
            metrics=[ExecutiveMetric.model_validate(row) for row in rows],
        )

    return router


def _validate_week_start(week_start: date | None) -> None:
    if week_start is not None and week_start.weekday() != 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="week_start must be a Monday (UTC ISO-week boundary)",
        )
