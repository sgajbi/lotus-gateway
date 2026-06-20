from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.contracts.foundation import (
    FoundationEvidenceSummary,
    FoundationPartialFailure,
    FoundationPerformanceSummary,
    FoundationRebalanceSummary,
    FoundationReportingReadiness,
    FoundationWorkflowLaunchCue,
)
from app.services.upstream_envelope import safe_upstream_detail

Number = int | float
UpstreamResult = tuple[int, dict[str, Any]]
GatheredResult = UpstreamResult | BaseException
OptionalUpstreamFailureContext = tuple[
    str,
    str,
    list[str],
    list[FoundationPartialFailure],
]


@dataclass(frozen=True)
class FoundationWorkspaceOptionalViews:
    performance: FoundationPerformanceSummary | None
    rebalance: FoundationRebalanceSummary | None
    reporting: FoundationReportingReadiness
    warnings: list[str]
    partial_failures: list[FoundationPartialFailure]


@dataclass(frozen=True)
class FoundationWorkspaceOptionalResults:
    performance_result: GatheredResult
    rebalance_result: GatheredResult
    reporting_result: GatheredResult


def build_foundation_workspace_optional_views(
    optional_results: FoundationWorkspaceOptionalResults,
) -> FoundationWorkspaceOptionalViews:
    warnings: list[str] = []
    partial_failures: list[FoundationPartialFailure] = []
    performance = parse_performance_result(
        result=optional_results.performance_result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    rebalance = parse_rebalance_result(
        result=optional_results.rebalance_result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    reporting = parse_reporting_result(
        result=optional_results.reporting_result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    return FoundationWorkspaceOptionalViews(
        performance=performance,
        rebalance=rebalance,
        reporting=reporting,
        warnings=warnings,
        partial_failures=partial_failures,
    )


def parse_performance_result(
    result: object,
    warnings: list[str],
    partial_failures: list[FoundationPartialFailure],
) -> FoundationPerformanceSummary | None:
    _, payload = unpack_optional_upstream(
        result=result,
        source_service="lotus-performance",
        unavailable_warning="FOUNDATION_PERFORMANCE_UNAVAILABLE",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if payload is None:
        return None

    results_by_period = payload.get("results_by_period", payload.get("resultsByPeriod", {}))
    if not isinstance(results_by_period, dict):
        warnings.append("FOUNDATION_PERFORMANCE_INVALID")
        return None

    period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period), None)
    if period_key is None:
        return None

    period_payload = results_by_period.get(period_key, {})
    if not isinstance(period_payload, dict):
        return None
    return FoundationPerformanceSummary(
        period=period_key,
        return_pct=extract_performance_return_pct(period_payload),
    )


def extract_performance_return_pct(period_payload: dict[str, Any]) -> Any | None:
    legacy_return = period_payload.get("net_cumulative_return")
    if isinstance(legacy_return, Number):
        return legacy_return

    portfolio_payload = period_payload.get("portfolio")
    if not isinstance(portfolio_payload, dict):
        return None
    summary = portfolio_payload.get("summary")
    if not isinstance(summary, dict):
        return None
    period_return = summary.get("period_return")
    if isinstance(period_return, dict):
        base_return = period_return.get("base")
        if isinstance(base_return, Number):
            return base_return
    cumulative_return = summary.get("cumulative_return")
    if isinstance(cumulative_return, dict):
        base_return = cumulative_return.get("base")
        if isinstance(base_return, Number):
            return base_return
    return None


def parse_rebalance_result(
    result: object,
    warnings: list[str],
    partial_failures: list[FoundationPartialFailure],
) -> FoundationRebalanceSummary | None:
    _, payload = unpack_optional_upstream(
        result=result,
        source_service="lotus-manage",
        unavailable_warning="FOUNDATION_REBALANCE_UNAVAILABLE",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if payload is None:
        return None

    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return FoundationRebalanceSummary(status="NOT_AVAILABLE")

    latest = items[0]
    if not isinstance(latest, dict):
        return FoundationRebalanceSummary(status="NOT_AVAILABLE")

    return FoundationRebalanceSummary(
        status=str(latest.get("status", "UNKNOWN")),
        last_run_at_utc=optional_str(latest.get("created_at")),
        last_rebalance_run_id=optional_str(latest.get("rebalance_run_id")),
    )


def parse_reporting_result(
    result: object,
    warnings: list[str],
    partial_failures: list[FoundationPartialFailure],
) -> FoundationReportingReadiness:
    _, payload = unpack_optional_upstream(
        result=result,
        source_service="lotus-report",
        unavailable_warning="FOUNDATION_REPORTING_UNAVAILABLE",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if payload is None:
        return FoundationReportingReadiness(status="UNAVAILABLE")

    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    generated_at = optional_str(payload.get("generatedAt"))
    status_value = "READY" if rows else "EMPTY"
    return FoundationReportingReadiness(
        status=status_value,
        generated_at_utc=generated_at,
        row_count=len(rows),
    )


def unpack_optional_upstream(
    result: object,
    source_service: str,
    unavailable_warning: str,
    warnings: list[str],
    partial_failures: list[FoundationPartialFailure],
) -> tuple[int | None, dict[str, Any] | None]:
    failure_context = (source_service, unavailable_warning, warnings, partial_failures)
    if isinstance(result, Exception):
        return unavailable_optional_upstream(
            None,
            "UPSTREAM_EXCEPTION",
            str(result),
            failure_context,
        )

    if not isinstance(result, tuple) or len(result) != 2:
        return unavailable_optional_upstream(
            None,
            "INVALID_UPSTREAM_RESPONSE",
            f"unexpected result type: {type(result)}",
            failure_context,
        )

    status_code, payload = result
    if not isinstance(payload, dict):
        return unavailable_optional_upstream(
            status_code,
            "INVALID_UPSTREAM_PAYLOAD",
            f"unexpected payload type: {type(payload)}",
            failure_context,
        )

    if status_code >= status.HTTP_400_BAD_REQUEST:
        return unavailable_optional_upstream(
            status_code,
            f"HTTP_{status_code}",
            safe_upstream_detail(payload, default_detail="optional upstream unavailable"),
            failure_context,
        )

    return status_code, payload


def unavailable_optional_upstream(
    status_code: int | None,
    error_code: str,
    detail: str,
    failure_context: OptionalUpstreamFailureContext,
) -> tuple[int | None, None]:
    source_service, unavailable_warning, warnings, partial_failures = failure_context
    partial_failures.append(
        FoundationPartialFailure(
            source_service=source_service,
            error_code=error_code,
            detail=detail,
        )
    )
    warnings.append(unavailable_warning)
    return status_code, None


def build_foundation_workflow_cues(portfolio_id: str) -> list[FoundationWorkflowLaunchCue]:
    return [
        FoundationWorkflowLaunchCue(
            key="performance",
            label="Open Performance",
            href=f"/app/performance?portfolioId={portfolio_id}",
        ),
        FoundationWorkflowLaunchCue(
            key="risk",
            label="Open Risk",
            href=f"/app/risk?portfolioId={portfolio_id}",
        ),
        FoundationWorkflowLaunchCue(
            key="proposal",
            label="Open Proposal",
            href=f"/app/proposal?portfolioId={portfolio_id}",
        ),
    ]


def build_foundation_evidence_summary(
    *,
    warnings: list[str],
    partial_failures: list[FoundationPartialFailure],
) -> FoundationEvidenceSummary:
    affected_sources = sorted({failure.source_service for failure in partial_failures})
    if partial_failures or warnings:
        return FoundationEvidenceSummary(
            status="partial",
            summary=(
                "Foundation workspace remains usable, but one or more upstream sources "
                "are degraded and should be reviewed before advisor use."
            ),
            warning_count=len(warnings),
            partial_failure_count=len(partial_failures),
            affected_sources=affected_sources,
        )
    return FoundationEvidenceSummary(
        status="ready",
        summary="Foundation workspace inputs are ready for advisor use.",
        warning_count=0,
        partial_failure_count=0,
        affected_sources=[],
    )


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
