from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from app.contracts.performance_evidence import (
    PerformanceCalculationEvidenceView,
    PerformanceEvidenceView,
    PerformanceSourceSupportabilityView,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_detail_capabilities import (
    SUPPORTED_ATTRIBUTION_DIMENSIONS,
    SUPPORTED_CONTRIBUTION_DIMENSIONS,
)
from app.services.performance_workspace_evidence_state import (
    EvidenceViewFetchState,
    EvidenceViewRequestContext,
)
from app.services.performance_workspace_evidence_supportability import (
    build_source_supportability as build_source_supportability,
)
from app.services.performance_workspace_evidence_supportability import (
    resolve_evidence_reason as resolve_evidence_reason,
)
from app.services.performance_workspace_evidence_supportability import (
    resolve_evidence_state as resolve_evidence_state,
)
from app.services.performance_workspace_failures import build_performance_failure


def resolve_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> PerformanceEvidenceView:
    if not fetch_state.requested_items:
        return build_empty_evidence_view_response(
            context=context,
            source_supportability=fetch_state.source_supportability,
        )
    if fetch_state.backed_count == 0:
        warnings.append("PERFORMANCE_EVIDENCE_UNAVAILABLE")
        return build_unavailable_evidence_view_response(
            context=context,
            fetch_state=fetch_state,
        )
    if fetch_state.complete_count == len(fetch_state.evidence_items):
        return build_supported_evidence_view_response(
            context=context,
            fetch_state=fetch_state,
        )
    record_partial_evidence_view(
        warnings=warnings,
        partial_failures=partial_failures,
    )
    return build_partial_evidence_view_response(
        context=context,
        fetch_state=fetch_state,
    )


def build_empty_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> PerformanceEvidenceView:
    return build_context_evidence_view(
        context=context,
        state="unavailable",
        reason="No durable calculation evidence is available for the current selection.",
        limitations=["No durable calculation evidence is available."],
        calculations=[],
        source_supportability=source_supportability,
    )


def build_unavailable_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    reason = "Gateway could not resolve execution or lineage evidence from lotus-performance."
    return build_context_evidence_view(
        context=context,
        state="unavailable",
        reason=reason,
        limitations=[reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def build_supported_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    evidence_state = resolve_evidence_state(
        evidence_state="supported",
        source_supportability=fetch_state.source_supportability,
    )
    evidence_reason = resolve_evidence_reason(
        evidence_state=evidence_state,
        supported_reason=(
            "Execution status, upstream lineage, and artifact inventory "
            "are exposed for the current performance view."
        ),
        source_supportability=fetch_state.source_supportability,
    )
    return build_context_evidence_view(
        context=context,
        state=evidence_state,
        reason=evidence_reason,
        limitations=[] if evidence_state == "supported" else [evidence_reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def build_partial_evidence_view_response(
    *,
    context: EvidenceViewRequestContext,
    fetch_state: EvidenceViewFetchState,
) -> PerformanceEvidenceView:
    reason = (
        "One or more performance calculations still have pending, failed, "
        "or unavailable lineage evidence."
    )
    return build_context_evidence_view(
        context=context,
        state="partial",
        reason=reason,
        limitations=[reason],
        calculations=fetch_state.evidence_items,
        source_supportability=fetch_state.source_supportability,
    )


def record_partial_evidence_view(
    *,
    warnings: list[str],
    partial_failures: list[WorkbenchPartialFailure],
) -> None:
    warnings.append("PERFORMANCE_EVIDENCE_PARTIAL")
    partial_failures.append(
        build_performance_failure(
            "lotus-performance",
            "PERFORMANCE_EVIDENCE_PARTIAL",
            (
                "Gateway resolved only partial execution or lineage evidence "
                "for one or more performance calculations."
            ),
        )
    )


def build_context_evidence_view(
    *,
    context: EvidenceViewRequestContext,
    state: str,
    reason: str,
    limitations: list[str],
    calculations: Sequence[PerformanceCalculationEvidenceView],
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> PerformanceEvidenceView:
    return build_performance_evidence_view(
        portfolio_id=context.portfolio_id,
        as_of_date=context.as_of_date,
        period=context.period,
        report_start_date=context.report_start_date,
        report_end_date=context.report_end_date,
        basis=context.basis,
        benchmark_code=context.benchmark_code,
        contract_version=context.contract_version,
        state=state,
        reason=reason,
        limitations=limitations,
        calculations=calculations,
        source_supportability=source_supportability,
    )


def build_performance_evidence_view(
    *,
    state: str,
    reason: str,
    as_of_date: str,
    period: str,
    report_start_date: str,
    report_end_date: str,
    basis: str,
    benchmark_code: str | None,
    contract_version: str,
    limitations: list[str],
    calculations: Sequence[PerformanceCalculationEvidenceView],
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
    portfolio_id: str | None = None,
) -> PerformanceEvidenceView:
    return PerformanceEvidenceView(
        state=state,
        as_of_date=as_of_date,
        period=period,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        basis=basis,
        benchmark_code=benchmark_code,
        calculation_scope="performance_workspace",
        source_services=build_evidence_source_services(
            calculations=calculations,
            source_supportability=source_supportability,
        ),
        input_freshness=build_evidence_input_freshness(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            benchmark_code=benchmark_code,
            calculations=calculations,
        ),
        methodology_references=["lotus-performance/docs/methodologies"],
        calculation_versions=build_evidence_calculation_versions(
            contract_version=contract_version,
            calculations=calculations,
        ),
        coverage=build_evidence_coverage(),
        fallbacks=build_evidence_fallbacks(calculations),
        limitations=limitations,
        generated_at=None,
        reason=reason,
        calculations=list(calculations),
        source_supportability=list(source_supportability),
    )


def build_evidence_source_services(
    *,
    calculations: Sequence[PerformanceCalculationEvidenceView],
    source_supportability: Sequence[PerformanceSourceSupportabilityView],
) -> list[str]:
    services = {
        item.source_service for item in source_supportability if item.source_service is not None
    }
    return sorted(services | ({"lotus-performance"} if calculations else set()))


def build_evidence_input_freshness(
    *,
    as_of_date: str,
    benchmark_code: str | None,
    calculations: Sequence[PerformanceCalculationEvidenceView],
    portfolio_id: str | None = None,
) -> dict[str, str]:
    def qualify(primary: set[str], related: set[str], identity: str | None) -> str:
        groups = [
            [s for s in item.upstream_snapshots if s.upstream_endpoint in related]
            for item in calculations
        ]
        if not groups or any(not any(s.upstream_endpoint in primary for s in g) for g in groups):
            return "unknown"
        snapshots = [s for group in groups for s in group]
        identifiers = {s.source_identifier for s in snapshots}
        if len(identifiers) != 1 or any(
            not value.strip() or value == "None" for value in identifiers
        ):
            return "unknown"
        if (identity is not None and identifiers != {identity}) or any(
            s.retrieval_status != "200" for s in snapshots
        ):
            return "unknown"
        try:
            dates = {s.as_of_date for s in snapshots} | {as_of_date}
            if any(date.fromisoformat(day).isoformat() != day for day in dates):
                return "unknown"
        except ValueError:
            return "unknown"
        return "fresh" if all(s.as_of_date == as_of_date for s in snapshots) else "stale"

    portfolio = {"portfolio_timeseries", "position_timeseries"}
    benchmark = {"benchmark_return_series", "benchmark_market_series"}
    input_freshness = {"performance": qualify(portfolio, portfolio, portfolio_id)}
    if benchmark_code:
        related = benchmark | {"benchmark_definition", "benchmark_composition_window"}
        input_freshness["benchmark"] = qualify(benchmark, related, benchmark_code)
    return input_freshness


def build_evidence_calculation_versions(
    *,
    contract_version: str,
    calculations: Sequence[PerformanceCalculationEvidenceView],
) -> dict[str, str]:
    calculation_versions = {"gateway_contract": contract_version}
    analytics_types = {
        item.analytics_type for item in calculations if item.analytics_type is not None
    }
    if analytics_types:
        calculation_versions["analytics_types"] = ",".join(sorted(analytics_types))
    return calculation_versions


def build_evidence_coverage() -> dict[str, list[str]]:
    dimensions = set(SUPPORTED_CONTRIBUTION_DIMENSIONS) | set(SUPPORTED_ATTRIBUTION_DIMENSIONS)
    return {
        "supported_dimensions": sorted(dimensions),
        "unsupported_dimensions": [
            dimension for dimension in ("issuer",) if dimension not in dimensions
        ],
    }


def build_evidence_fallbacks(
    calculations: Sequence[PerformanceCalculationEvidenceView],
) -> list[str]:
    return [item.reason for item in calculations if item.reason is not None and item.reason.strip()]
