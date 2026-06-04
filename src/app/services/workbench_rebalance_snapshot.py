from datetime import UTC, datetime
from typing import Any

from fastapi import status

from app.contracts.portfolio import PortfolioRebalanceSupportabilitySummary
from app.contracts.workbench import (
    WorkbenchPartialFailure,
    WorkbenchRebalanceRunSummary,
    WorkbenchRebalanceSnapshot,
)


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
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-manage",
                error_code="UPSTREAM_EXCEPTION",
                detail=str(result),
            )
        )
        warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
        return None

    if not isinstance(result, tuple) or len(result) != 2:
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-manage",
                error_code="INVALID_UPSTREAM_RESPONSE",
                detail=f"unexpected result type: {type(result)}",
            )
        )
        warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
        return None

    dpm_status, dpm_payload = result
    if not isinstance(dpm_payload, dict):
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-manage",
                error_code="INVALID_UPSTREAM_PAYLOAD",
                detail=f"unexpected payload type: {type(dpm_payload)}",
            )
        )
        warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
        return None

    if dpm_status >= status.HTTP_400_BAD_REQUEST:
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-manage",
                error_code=f"HTTP_{dpm_status}",
                detail=str(dpm_payload.get("detail", dpm_payload)),
            )
        )
        warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
        return None

    return dpm_payload


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
        last_rebalance_run_id=_optional_str(latest.get("rebalance_run_id")),
        last_run_at_utc=_optional_datetime_str(latest.get("created_at")),
        supportability=_parse_rebalance_supportability(
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
                rebalance_run_id=_optional_str(item.get("rebalance_run_id")),
                status=str(item.get("status", "UNKNOWN")),
                created_at_utc=_optional_datetime_str(item.get("created_at")),
                error_code=_extract_dpm_run_error_code(item),
                workflow_state=_optional_str(
                    item.get("workflow_state")
                    or item.get("workflow_decision_state")
                    or item.get("review_state")
                ),
            )
        )
    return recent_runs


def _parse_rebalance_supportability(
    dpm_payload: dict[str, Any],
    *,
    supportability_result: object | None = None,
    partial_failures: list[WorkbenchPartialFailure] | None = None,
    warnings: list[str] | None = None,
) -> PortfolioRebalanceSupportabilitySummary | None:
    supportability_payload = _extract_rebalance_supportability_payload(
        dpm_payload=dpm_payload,
        supportability_result=supportability_result,
        partial_failures=partial_failures,
        warnings=warnings,
    )
    if not isinstance(supportability_payload, dict):
        return None
    return PortfolioRebalanceSupportabilitySummary(
        feature_key=(
            _optional_str(supportability_payload.get("feature_key"))
            or "manage.observability.action_register_supportability"
        ),
        state=str(supportability_payload.get("state") or "unknown"),
        reason=_optional_str(supportability_payload.get("reason")),
        freshness_bucket=_optional_str(supportability_payload.get("freshness_bucket")),
        run_count=_optional_int(supportability_payload.get("run_count")),
        operation_count=_optional_int(supportability_payload.get("operation_count")),
        workflow_decision_count=_optional_int(
            supportability_payload.get("workflow_decision_count")
        ),
    )


def _extract_rebalance_supportability_payload(
    *,
    dpm_payload: dict[str, Any],
    supportability_result: object | None,
    partial_failures: list[WorkbenchPartialFailure] | None,
    warnings: list[str] | None,
) -> dict[str, Any] | None:
    supportability_payload = dpm_payload.get("supportability")
    if isinstance(supportability_payload, dict):
        return supportability_payload
    if supportability_result is None:
        return None
    if isinstance(supportability_result, BaseException):
        if partial_failures is not None:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code="SUPPORTABILITY_SUMMARY_UNAVAILABLE",
                    detail=str(supportability_result),
                )
            )
        if warnings is not None:
            warnings.append("MANAGE_REBALANCE_SUPPORTABILITY_UNAVAILABLE")
        return None
    if not isinstance(supportability_result, tuple) or len(supportability_result) != 2:
        if partial_failures is not None:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code="INVALID_SUPPORTABILITY_SUMMARY_RESULT",
                    detail=f"unexpected supportability result: {type(supportability_result)}",
                )
            )
        if warnings is not None:
            warnings.append("MANAGE_REBALANCE_SUPPORTABILITY_UNAVAILABLE")
        return None
    supportability_status, supportability_summary = supportability_result
    if not isinstance(supportability_status, int) or not isinstance(
        supportability_summary,
        dict,
    ):
        if partial_failures is not None:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code="INVALID_SUPPORTABILITY_SUMMARY_PAYLOAD",
                    detail=(
                        "supportability summary result must include integer status "
                        "and object payload"
                    ),
                )
            )
        if warnings is not None:
            warnings.append("MANAGE_REBALANCE_SUPPORTABILITY_UNAVAILABLE")
        return None
    if supportability_status >= status.HTTP_400_BAD_REQUEST:
        if partial_failures is not None:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code=f"SUPPORTABILITY_HTTP_{supportability_status}",
                    detail=str(supportability_summary.get("detail", supportability_summary)),
                )
            )
        if warnings is not None:
            warnings.append("MANAGE_REBALANCE_SUPPORTABILITY_UNAVAILABLE")
        return None
    supportability_payload = supportability_summary.get("supportability")
    if isinstance(supportability_payload, dict):
        merged_payload = dict(supportability_payload)
        for summary_key in ("run_count", "operation_count", "workflow_decision_count"):
            if summary_key not in merged_payload and summary_key in supportability_summary:
                merged_payload[summary_key] = supportability_summary[summary_key]
        return merged_payload
    return None


def _extract_dpm_run_error_code(item: dict[str, Any]) -> str | None:
    for key in ("error_code", "failure_code", "reason_code"):
        value = _optional_str(item.get(key))
        if value:
            return value
    error_payload = item.get("error")
    if isinstance(error_payload, dict):
        return _optional_str(error_payload.get("code"))
    return None


def _optional_datetime_str(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
