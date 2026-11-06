"""Public reporting-pipeline interfaces consumed by the reporting HTTP service.

The service reads the pipeline's restricted execution JSONL audit log and uses
Prefect's public flow object for operator-triggered runs. No ETL logic is
implemented here.
"""

from __future__ import annotations

import json
import fcntl
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class PipelineInterfaceError(RuntimeError):
    """The reporting pipeline cannot be safely accessed by the API process."""


def _pipeline_module():
    """Import the existing pipeline without requiring an installed package."""
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in os.sys.path:
        os.sys.path.insert(0, str(project_root))
    try:
        from data.pipelines import pipeline
    except ImportError as exc:
        raise PipelineInterfaceError(
            "The executive reporting pipeline is not installed in this API image"
        ) from exc
    return pipeline


def get_executive_report_status(week_start: date | None = None) -> dict[str, Any]:
    """Return the most recent audited run, optionally scoped to an ISO week."""
    pipeline = _pipeline_module()
    path = pipeline.RUN_LOG_PATH
    if not path.exists():
        return {"status": "not_run", "run": None}

    latest: dict[str, Any] | None = None
    latest_started: datetime | None = None
    try:
        with path.open(encoding="utf-8") as log_file:
            for line in log_file:
                if not line.strip():
                    continue
                record = json.loads(line)
                if week_start is not None and record.get("week_start") != week_start.isoformat():
                    continue
                started = datetime.fromisoformat(record["started_at"])
                if latest_started is None or started >= latest_started:
                    latest = record
                    latest_started = started
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PipelineInterfaceError("Pipeline run metadata is unavailable or invalid") from exc

    if latest is None:
        return {"status": "not_run", "run": None}
    return {"status": latest.get("status", "unknown"), "run": latest}


def request_executive_weekly_report(
    week_start: date,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Dispatch the named Prefect flow for a single Monday-bounded week."""
    if week_start.weekday() != 0:
        raise ValueError("week_start must be a Monday (UTC ISO-week boundary)")
    if idempotency_key is not None and not idempotency_key.strip():
        raise ValueError("Idempotency-Key must not be blank")

    pipeline = _pipeline_module()
    key = idempotency_key or str(uuid4())
    pipeline.RUN_LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = pipeline.RUN_LOG_PATH.with_suffix(".lock")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        # Serialize checks/dispatches across API worker processes so duplicate
        # client requests with the same key cannot start concurrent flows.
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        # Same client key + week is idempotent while the original run is active
        # or after it completes. A different key explicitly requests a rerun.
        for record in _read_run_records(pipeline.RUN_LOG_PATH):
            if (
                record.get("week_start") == week_start.isoformat()
                and record.get("idempotency_key") == key
            ):
                return {
                    "status": record.get("status", "unknown"),
                    "run": record,
                    "deduplicated": True,
                }

        try:
            result = pipeline.executive_weekly_report_flow(
                week_start,
                trigger_type="manual",
                idempotency_key=key,
            )
        except PipelineInterfaceError:
            raise
        except Exception as exc:
            # Prefect flow exceptions may include task details or configuration.
            raise PipelineInterfaceError("Executive reporting flow failed") from exc
        return {
            "status": result.get("status", "completed"),
            "run": result,
            "deduplicated": False,
        }
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _read_run_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as log_file:
            return [json.loads(line) for line in log_file if line.strip()]
    except (OSError, ValueError) as exc:
        raise PipelineInterfaceError("Pipeline run metadata is unavailable or invalid") from exc


__all__ = [
    "PipelineInterfaceError",
    "get_executive_report_status",
    "request_executive_weekly_report",
]
