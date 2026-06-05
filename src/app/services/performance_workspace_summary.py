from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_attribution import build_workspace_attribution_summary
from app.services.performance_workspace_chart_points import build_workspace_chart_points
from app.services.performance_workspace_contribution import build_workspace_contribution_summary
from app.services.performance_workspace_failures import build_performance_failure
from app.services.performance_workspace_mwr import build_workspace_mwr_summary
from app.services.performance_workspace_parsing import safe_str
from app.services.performance_workspace_returns import (
    build_workspace_comparative_summary,
    extract_twr_workspace_block,
    resolve_results_period_key,
)
from app.services.upstream_envelope import safe_upstream_detail

UpstreamPayload: TypeAlias = dict[str, Any]
UpstreamResult: TypeAlias = tuple[int, UpstreamPayload]
GatheredResult: TypeAlias = UpstreamResult | BaseException


@dataclass(frozen=True)
class ParsedWorkspaceSummary:
    net_performance: PerformanceComparativeSummary
    gross_performance: PerformanceComparativeSummary
    net_chart: list[PerformanceChartPoint]
    gross_chart: list[PerformanceChartPoint]
    money_weighted_return: MoneyWeightedReturnSummary | None
    contribution: ContributionSummaryView | None
    attribution: AttributionSummaryView | None
    resolved_benchmark_code: str | None

    @classmethod
    def empty(cls) -> ParsedWorkspaceSummary:
        return cls(
            net_performance=PerformanceComparativeSummary(metric_basis="NET"),
            gross_performance=PerformanceComparativeSummary(metric_basis="GROSS"),
            net_chart=[],
            gross_chart=[],
            money_weighted_return=None,
            contribution=None,
            attribution=None,
            resolved_benchmark_code=None,
        )


@dataclass(frozen=True)
class WorkspaceSummaryBlocks:
    period_payload: dict[str, Any]
    benchmark_block: dict[str, Any]
    active_block: dict[str, Any]
    net_block: dict[str, Any]
    gross_block: dict[str, Any]


def parse_workspace_summary_result(
    *,
    result: GatheredResult,
    requested_period: str,
    chart_frequency: str,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> ParsedWorkspaceSummary:
    empty_summary = ParsedWorkspaceSummary.empty()
    payload = workspace_summary_payload_from_result(
        result=result,
        warnings=warnings,
        partial_failures=partial_failures,
    )
    if payload is None:
        return empty_summary

    period_payload = workspace_summary_period_payload(
        payload=payload,
        requested_period=requested_period,
        warnings=warnings,
    )
    if period_payload is None:
        return empty_summary

    return build_parsed_workspace_summary(
        blocks=workspace_summary_blocks(period_payload),
        chart_frequency=chart_frequency,
    )


def workspace_summary_payload_from_result(
    *,
    result: GatheredResult,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> dict[str, Any] | None:
    if isinstance(result, BaseException):
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
        )
        return None

    status_code, payload = result
    if not isinstance(payload, dict):
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
        return None
    if status_code >= 400:
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_UNAVAILABLE")
        partial_failures.append(
            build_performance_failure(
                "lotus-performance",
                f"HTTP_{status_code}",
                safe_upstream_detail(payload, default_detail="workspace summary unavailable"),
            )
        )
        return None
    return payload


def workspace_summary_period_payload(
    *,
    payload: dict[str, Any],
    requested_period: str,
    warnings: list[str],
) -> dict[str, Any] | None:
    results_by_period = payload.get("results_by_period", {})
    if not isinstance(results_by_period, dict) or not results_by_period:
        warnings.append("PERFORMANCE_WORKSPACE_SUMMARY_INVALID")
        return None

    period_key = resolve_results_period_key(
        requested_period=requested_period,
        results_by_period=results_by_period,
    )
    period_payload = results_by_period.get(period_key, {})
    if not isinstance(period_payload, dict):
        return None
    return period_payload


def workspace_summary_blocks(period_payload: dict[str, Any]) -> WorkspaceSummaryBlocks:
    benchmark_block = period_payload.get("benchmark", {})
    active_block = period_payload.get("active", {})
    return WorkspaceSummaryBlocks(
        period_payload=period_payload,
        benchmark_block=benchmark_block if isinstance(benchmark_block, dict) else {},
        active_block=active_block if isinstance(active_block, dict) else {},
        net_block=extract_twr_workspace_block(period_payload, "net"),
        gross_block=extract_twr_workspace_block(period_payload, "gross"),
    )


def build_parsed_workspace_summary(
    *,
    blocks: WorkspaceSummaryBlocks,
    chart_frequency: str,
) -> ParsedWorkspaceSummary:
    net_performance = build_workspace_comparative_summary(
        metric_basis="NET",
        portfolio_block=blocks.net_block,
        benchmark_block=blocks.benchmark_block,
        active_basis_block=blocks.active_block.get("net", {}),
    )
    gross_performance = build_workspace_comparative_summary(
        metric_basis="GROSS",
        portfolio_block=blocks.gross_block,
        benchmark_block=blocks.benchmark_block,
        active_basis_block=blocks.active_block.get("gross", {}),
    )
    net_chart = build_workspace_chart_points(
        portfolio_block=blocks.net_block,
        benchmark_block=blocks.benchmark_block,
        chart_frequency=chart_frequency,
    )
    gross_chart = build_workspace_chart_points(
        portfolio_block=blocks.gross_block,
        benchmark_block=blocks.benchmark_block,
        chart_frequency=chart_frequency,
    )

    return ParsedWorkspaceSummary(
        net_performance=net_performance,
        gross_performance=gross_performance,
        net_chart=net_chart,
        gross_chart=gross_chart,
        money_weighted_return=build_workspace_mwr_summary(blocks.period_payload),
        contribution=build_workspace_contribution_summary(blocks.period_payload),
        attribution=build_workspace_attribution_summary(blocks.period_payload),
        resolved_benchmark_code=safe_str(blocks.benchmark_block.get("benchmark_id")),
    )
