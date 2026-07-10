from datetime import UTC, datetime
from typing import Any

from fastapi import status

from app.contracts.workbench import (
    WorkbenchPartialFailure,
    WorkbenchRebalanceRunSummary,
    WorkbenchRebalanceSnapshot,
)
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workbench_rebalance_supportability import parse_rebalance_supportability
from app.services.workbench_rebalance_values import optional_str


def parse_rebalance_snapshot(
    result: object,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
    supportability_result: object | None = None,
) -> WorkbenchRebalanceSnapshot | None:
    dpm_payload = _unpack_rebalance_payload(
        result=result,
        partial_failures=partial_failures,
        warnings=warnings,
    )
    if dpm_payload is None:
        return None

    items = dpm_payload.get("items", [])
    if not isinstance(items, list) or not items:
        return WorkbenchRebalanceSnapshot(status="NOT_AVAILABLE")

    latest = _latest_rebalance_run(items)
    if latest is None:
        return WorkbenchRebalanceSnapshot(status="NOT_AVAILABLE")

    return _build_rebalance_snapshot(
        latest=latest,
        items=items,
        dpm_payload=dpm_payload,
        supportability_result=supportability_result,
        partial_failures=partial_failures,
        warnings=warnings,
    )


def _unpack_rebalance_payload(
    *,
    result: object,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
) -> dict[str, Any] | None:
    if isinstance(result, Exception):
        return _rebalance_unavailable_payload(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code="UPSTREAM_EXCEPTION",
            detail=str(result),
        )

    if not isinstance(result, tuple) or len(result) != 2:
        return _rebalance_unavailable_payload(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code="INVALID_UPSTREAM_RESPONSE",
            detail=f"unexpected result type: {type(result)}",
        )

    dpm_status, dpm_payload = result
    if not isinstance(dpm_payload, dict):
        return _rebalance_unavailable_payload(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code="INVALID_UPSTREAM_PAYLOAD",
            detail=f"unexpected payload type: {type(dpm_payload)}",
        )

    if dpm_status >= status.HTTP_400_BAD_REQUEST:
        return _rebalance_unavailable_payload(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code=f"HTTP_{dpm_status}",
            detail=safe_upstream_detail(
                dpm_payload,
                default_detail="rebalance snapshot unavailable",
            ),
        )

    return dpm_payload


def _rebalance_unavailable_payload(
    *,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
    error_code: str,
    detail: str,
) -> dict[str, Any] | None:
    _record_rebalance_unavailable(
        partial_failures=partial_failures,
        warnings=warnings,
        error_code=error_code,
        detail=detail,
    )
    return None


def _record_rebalance_unavailable(
    *,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
    error_code: str,
    detail: str,
) -> None:
    partial_failures.append(
        WorkbenchPartialFailure(
            source_service="lotus-manage",
            error_code=error_code,
            detail=detail,
        )
    )
    warnings.append("MANAGE_REBALANCE_UNAVAILABLE")


def _latest_rebalance_run(items: list[Any]) -> dict[str, Any] | None:
    latest = items[0]
    return latest if isinstance(latest, dict) else None


def _build_rebalance_snapshot(
    *,
    latest: dict[str, Any],
    items: list[Any],
    dpm_payload: dict[str, Any],
    supportability_result: object | None,
    partial_failures: list[WorkbenchPartialFailure],
    warnings: list[str],
) -> WorkbenchRebalanceSnapshot:
    return WorkbenchRebalanceSnapshot(
        status=str(latest.get("status", "UNKNOWN")),
        last_rebalance_run_id=optional_str(latest.get("rebalance_run_id")),
        last_run_at_utc=_optional_datetime_str(latest.get("created_at")),
        supportability=parse_rebalance_supportability(
            dpm_payload,
            supportability_result=supportability_result,
            partial_failures=partial_failures,
            warnings=warnings,
        ),
        recent_runs=_parse_recent_dpm_runs(items),
    )


def _parse_recent_dpm_runs(items: list[Any]) -> list[WorkbenchRebalanceRunSummary]:
    recent_runs: list[WorkbenchRebalanceRunSummary] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        recent_runs.append(
            WorkbenchRebalanceRunSummary(
                rebalance_run_id=optional_str(item.get("rebalance_run_id")),
                status=str(item.get("status", "UNKNOWN")),
                created_at_utc=_optional_datetime_str(item.get("created_at")),
                error_code=_extract_dpm_run_error_code(item),
                workflow_state=optional_str(
                    item.get("workflow_state")
                    or item.get("workflow_decision_state")
                    or item.get("review_state")
                ),
            )
        )
    return recent_runs


def _extract_dpm_run_error_code(item: dict[str, Any]) -> str | None:
    for key in ("error_code", "failure_code", "reason_code"):
        value = optional_str(item.get(key))
        if value:
            return value
    error_payload = item.get("error")
    if isinstance(error_payload, dict):
        return optional_str(error_payload.get("code"))
    return None


def _optional_datetime_str(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return None
