from typing import Any

from fastapi import status

from app.contracts.portfolio_workspace import PortfolioRebalanceSupportabilitySummary
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workbench_rebalance_values import optional_int, optional_str


def parse_rebalance_supportability(
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
            optional_str(supportability_payload.get("feature_key"))
            or "manage.observability.action_register_supportability"
        ),
        state=str(supportability_payload.get("state") or "unknown"),
        reason=optional_str(supportability_payload.get("reason")),
        freshness_bucket=optional_str(supportability_payload.get("freshness_bucket")),
        run_count=optional_int(supportability_payload.get("run_count")),
        operation_count=optional_int(supportability_payload.get("operation_count")),
        workflow_decision_count=optional_int(supportability_payload.get("workflow_decision_count")),
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
    supportability_summary = _unpack_rebalance_supportability_summary(
        supportability_result=supportability_result,
        partial_failures=partial_failures,
        warnings=warnings,
    )
    if supportability_summary is None:
        return None
    return _supportability_payload_from_summary(supportability_summary)


def _unpack_rebalance_supportability_summary(
    *,
    supportability_result: object,
    partial_failures: list[WorkbenchPartialFailure] | None,
    warnings: list[str] | None,
) -> dict[str, Any] | None:
    if isinstance(supportability_result, BaseException):
        _record_rebalance_supportability_unavailable(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code="SUPPORTABILITY_SUMMARY_UNAVAILABLE",
            detail=str(supportability_result),
        )
        return None
    if not isinstance(supportability_result, tuple) or len(supportability_result) != 2:
        _record_rebalance_supportability_unavailable(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code="INVALID_SUPPORTABILITY_SUMMARY_RESULT",
            detail=f"unexpected supportability result: {type(supportability_result)}",
        )
        return None
    supportability_status, supportability_summary = supportability_result
    if not isinstance(supportability_status, int) or not isinstance(
        supportability_summary,
        dict,
    ):
        _record_rebalance_supportability_unavailable(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code="INVALID_SUPPORTABILITY_SUMMARY_PAYLOAD",
            detail=("supportability summary result must include integer status and object payload"),
        )
        return None
    if supportability_status >= status.HTTP_400_BAD_REQUEST:
        _record_rebalance_supportability_unavailable(
            partial_failures=partial_failures,
            warnings=warnings,
            error_code=f"SUPPORTABILITY_HTTP_{supportability_status}",
            detail=safe_upstream_detail(
                supportability_summary,
                default_detail="rebalance supportability unavailable",
            ),
        )
        return None
    return supportability_summary


def _supportability_payload_from_summary(
    supportability_summary: dict[str, Any],
) -> dict[str, Any] | None:
    supportability_payload = supportability_summary.get("supportability")
    if isinstance(supportability_payload, dict):
        merged_payload = dict(supportability_payload)
        _merge_supportability_summary_counts(
            merged_payload=merged_payload,
            supportability_summary=supportability_summary,
        )
        return merged_payload
    return None


def _merge_supportability_summary_counts(
    *,
    merged_payload: dict[str, Any],
    supportability_summary: dict[str, Any],
) -> None:
    for summary_key in ("run_count", "operation_count", "workflow_decision_count"):
        if summary_key not in merged_payload and summary_key in supportability_summary:
            merged_payload[summary_key] = supportability_summary[summary_key]


def _record_rebalance_supportability_unavailable(
    *,
    partial_failures: list[WorkbenchPartialFailure] | None,
    warnings: list[str] | None,
    error_code: str,
    detail: str,
) -> None:
    if partial_failures is not None:
        partial_failures.append(
            WorkbenchPartialFailure(
                source_service="lotus-manage",
                error_code=error_code,
                detail=detail,
            )
        )
    if warnings is not None:
        warnings.append("MANAGE_REBALANCE_SUPPORTABILITY_UNAVAILABLE")
