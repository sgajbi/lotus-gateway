from __future__ import annotations

from typing import Any

from app.clients.lotus_ai_client import LotusAiClient
from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefResponse,
    AdvisorBriefSourceMetric,
    AdvisorBriefStatus,
    AdvisorBriefSupportabilityItem,
    AdvisorBriefTone,
)
from app.contracts.performance_workspace import (
    AttributionSummaryView,
    ContributionPositionView,
    ContributionSummaryView,
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.middleware.server_timing import server_timing_span
from app.services.performance_workspace_service import PerformanceWorkspaceService

_TASK_ID = "explain.v1"
_EXPECTED_OUTPUT_LABEL = "EXPLANATION_ONLY"


class AdvisorBriefService:
    def __init__(
        self,
        *,
        performance_workspace_service: PerformanceWorkspaceService,
        lotus_ai_client: LotusAiClient,
    ):
        self._performance_workspace_service = performance_workspace_service
        self._lotus_ai_client = lotus_ai_client

    async def get_performance_advisor_brief(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
    ) -> AdvisorBriefResponse:
        async with server_timing_span("perf-advisor-brief-source"):
            workspace = (
                await self._performance_workspace_service.get_performance_workspace(
                    portfolio_id=portfolio_id,
                    correlation_id=correlation_id,
                    period=period,
                    chart_frequency=chart_frequency,
                    contribution_dimension=contribution_dimension,
                    attribution_dimension=attribution_dimension,
                    detail_basis=detail_basis,
                    benchmark_code=benchmark_code,
                    explicit_start_date=explicit_start_date,
                    explicit_end_date=explicit_end_date,
                )
            )

        selected_performance = (
            workspace.net_performance
            if detail_basis.upper() == "NET"
            else workspace.gross_performance
        )
        source_refs = _build_source_refs(workspace=workspace)
        supportability = _build_supportability(workspace=workspace)
        status = _resolve_status(workspace=workspace, supportability=supportability)

        source_summary = _build_source_summary(
            workspace=workspace,
            selected_performance=selected_performance,
        )
        talking_points = _build_source_talking_points(
            workspace=workspace,
            selected_performance=selected_performance,
        )
        recommended_actions = _build_recommended_actions(workspace=workspace)
        risks_and_exceptions = _build_risks_and_exceptions(
            workspace=workspace,
            supportability=supportability,
        )
        ai_audit: dict[str, Any] = _normalize_ai_audit({})
        ai_evidence: dict[str, Any] = {"descriptors": []}

        if status is not AdvisorBriefStatus.UNAVAILABLE:
            async with server_timing_span("perf-advisor-brief-ai"):
                ai_status, ai_payload = await self._lotus_ai_client.execute_task(
                    task_id=_TASK_ID,
                    caller_app="lotus-gateway",
                    correlation_id=correlation_id,
                    context_summary=(
                        f"Advisor brief context for portfolio {workspace.portfolio_id}, "
                        f"{workspace.period} period, basis {workspace.detail_basis}."
                    ),
                    context_payload=_build_ai_fact_bundle(
                        workspace=workspace,
                        selected_performance=selected_performance,
                    ),
                    source_refs=source_refs,
                    expected_output_label=_EXPECTED_OUTPUT_LABEL,
                )
            if ai_status == 200 and ai_payload.get("status") == "COMPLETED":
                result = _safe_dict(ai_payload.get("result"))
                structured_output = _safe_dict(result.get("structured_output"))
                source_summary = (
                    _extract_ai_summary(ai_payload=ai_payload, structured_output=structured_output)
                    or source_summary
                )
                talking_points = (
                    _extract_ai_talking_points(
                        structured_output=structured_output,
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                    or talking_points
                )
                recommended_actions = (
                    _extract_ai_recommended_actions(
                        structured_output=structured_output,
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                    or recommended_actions
                )
                risks_and_exceptions = (
                    _extract_ai_risks(
                        structured_output=structured_output,
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                    or risks_and_exceptions
                )
                ai_audit = _normalize_ai_audit(_safe_dict(ai_payload.get("audit")))
                ai_evidence = _safe_dict(ai_payload.get("evidence")) or {"descriptors": []}
            else:
                status = AdvisorBriefStatus.PARTIAL
                ai_audit = _normalize_ai_audit(
                    {
                        "task_id": _TASK_ID,
                        "output_label": _EXPECTED_OUTPUT_LABEL,
                        "provider_mode": "unavailable",
                        "detail": _safe_error_detail(ai_payload),
                    }
                )
                risks_and_exceptions.append(
                    AdvisorBriefNarrativeItem(
                        headline="AI narrative generation is unavailable.",
                        detail=(
                            "Source-backed metrics remain available for manual review and "
                            "client prep."
                        ),
                        tone=AdvisorBriefTone.WARNING,
                        evidence_refs=[
                            _summary_evidence_ref(
                                label="Advisor Brief",
                                value="Unavailable",
                                portfolio_id=workspace.portfolio_id,
                                period=workspace.period,
                                basis=workspace.detail_basis,
                                benchmark_code=workspace.benchmark_code,
                            )
                        ],
                    )
                )

        return AdvisorBriefResponse(
            correlation_id=correlation_id,
            contract_version=workspace.contract_version,
            portfolio_id=workspace.portfolio_id,
            portfolio=workspace.portfolio,
            as_of_date=workspace.as_of_date,
            period=workspace.period,
            report_start_date=workspace.report_start_date,
            report_end_date=workspace.report_end_date,
            detail_basis=workspace.detail_basis,
            chart_frequency=workspace.chart_frequency,
            contribution_dimension=workspace.contribution_dimension,
            attribution_dimension=workspace.attribution_dimension,
            benchmark_code=workspace.benchmark_code,
            status=status,
            summary=source_summary,
            talking_points=talking_points,
            recommended_actions=recommended_actions,
            risks_and_exceptions=risks_and_exceptions,
            source_metrics=_build_source_metrics(
                workspace=workspace,
                selected_performance=selected_performance,
            ),
            supportability=supportability,
            ai_audit=ai_audit,
            ai_evidence=ai_evidence,
            warnings=workspace.warnings,
            partial_failures=workspace.partial_failures,
        )


def _normalize_ai_audit(audit: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(audit)
    normalized.setdefault("task_id", _TASK_ID)
    normalized.setdefault("output_label", _EXPECTED_OUTPUT_LABEL)
    normalized.setdefault("provider_mode", "unknown")
    normalized.setdefault("provider_id", None)
    normalized.setdefault("adapter_kind", None)
    normalized.setdefault("model_id", None)
    normalized.setdefault("generated_at", None)
    normalized.setdefault("stubbed", True)
    normalized.setdefault("source_refs", [])
    return normalized


def _build_source_refs(*, workspace: PerformanceWorkspaceResponse) -> list[str]:
    refs = [
        f"lotus-gateway:workbench:{workspace.portfolio_id}:performance-summary:{workspace.period}",
        f"lotus-gateway:workbench:{workspace.portfolio_id}:performance-details:{workspace.period}",
    ]
    if workspace.benchmark_code:
        refs.append(
            f"lotus-performance:benchmark:{workspace.portfolio_id}:{workspace.benchmark_code}:{workspace.period}"
        )
    return refs


def _build_ai_fact_bundle(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> dict[str, Any]:
    contribution = workspace.contribution
    attribution = workspace.attribution
    return {
        "portfolio": _build_ai_portfolio_context(workspace=workspace),
        "period": {
            "period": workspace.period,
            "report_start_date": workspace.report_start_date,
            "report_end_date": workspace.report_end_date,
            "as_of_date": workspace.as_of_date,
            "detail_basis": workspace.detail_basis,
        },
        "benchmark": {
            "benchmark_code": workspace.benchmark_code,
            "benchmark_name": _benchmark_display_label(workspace=workspace),
            "benchmark_return_pct": selected_performance.benchmark_return_pct,
        },
        "performance": {
            "portfolio_return_pct": selected_performance.portfolio_return_pct,
            "benchmark_return_pct": selected_performance.benchmark_return_pct,
            "active_return_pct": selected_performance.active_return_pct,
            "net_cash_flow": selected_performance.net_cash_flow,
            "end_market_value": selected_performance.end_market_value,
            "money_weighted_return_pct": (
                workspace.money_weighted_return.money_weighted_return_pct
                if workspace.money_weighted_return
                else None
            ),
        },
        "contribution": {
            "portfolio_contribution_pct": (
                contribution.portfolio_contribution_pct if contribution else None
            ),
            "coverage_mv_pct": contribution.coverage_mv_pct if contribution else None,
            "top_positions": [
                _build_ai_contribution_position(row=row)
                for row in _positive_position_contributors(contribution=contribution)[:5]
            ],
            "bottom_positions": [
                _build_ai_contribution_position(row=row)
                for row in _negative_position_contributors(contribution=contribution)[:5]
            ],
        },
        "attribution": {
            "active_return_pct": attribution.active_return_pct if attribution else None,
            "sum_of_effects_pct": attribution.sum_of_effects_pct if attribution else None,
            "residual_pct": attribution.residual_pct if attribution else None,
            "top_effects": _top_attribution_effects(attribution=attribution),
        },
        "supportability": [
            item.model_dump(mode="json")
            for item in _build_supportability(workspace=workspace)
        ],
        "warnings": workspace.warnings,
        "partial_failures": [item.model_dump(mode="json") for item in workspace.partial_failures],
    }


def _build_ai_portfolio_context(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> dict[str, Any]:
    return {
        "portfolio_id": workspace.portfolio_id,
        "display_label": _portfolio_display_label(workspace=workspace),
        "base_currency": workspace.portfolio.base_currency,
        "booking_center_code": workspace.portfolio.booking_center_code,
        "client_id": workspace.portfolio.client_id,
    }


def _build_ai_contribution_position(
    *,
    row: ContributionPositionView,
) -> dict[str, Any]:
    return {
        "display_label": _normalize_position_label(row.position_id),
        "contribution_pct": row.contribution_pct,
        "weight_avg_pct": row.weight_avg_pct,
        "total_return_pct": row.total_return_pct,
        "local_contribution_pct": row.local_contribution_pct,
        "fx_contribution_pct": row.fx_contribution_pct,
    }


def _build_source_summary(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> str:
    portfolio_return = _format_pct(selected_performance.portfolio_return_pct)
    benchmark_return = _format_pct(selected_performance.benchmark_return_pct)
    active_return = _format_pct(selected_performance.active_return_pct)
    if (
        selected_performance.portfolio_return_pct is None
        and selected_performance.benchmark_return_pct is None
    ):
        return (
            "No source-backed advisor brief can be generated from the current performance "
            "selection."
    )
    return (
        f"{workspace.period} portfolio return for {_portfolio_display_label(workspace=workspace)} "
        f"is {portfolio_return} versus "
        f"{_benchmark_display_label(workspace=workspace) or 'benchmark'} {benchmark_return}, "
        f"with active return {active_return}."
    )


def _extract_ai_summary(
    *,
    ai_payload: dict[str, Any],
    structured_output: dict[str, Any] | None = None,
) -> str | None:
    output_payload = structured_output or _safe_dict(
        _safe_dict(ai_payload.get("result")).get("structured_output")
    )
    summary = output_payload.get("grounded_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    result = _safe_dict(ai_payload.get("result"))
    message = result.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def _extract_ai_talking_points(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefNarrativeItem]:
    return [
        item
        for item in (
            _parse_ai_narrative_item(value=value, route=route, default_mode="summary")
            for value in _safe_list(structured_output.get("talking_points"))
        )
        if item is not None
    ]


def _extract_ai_risks(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefNarrativeItem]:
    return [
        item
        for item in (
            _parse_ai_narrative_item(value=value, route=route, default_mode="analysis")
            for value in _safe_list(structured_output.get("risks_and_exceptions"))
        )
        if item is not None
    ]


def _extract_ai_recommended_actions(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefActionItem]:
    actions: list[AdvisorBriefActionItem] = []
    for value in _safe_list(structured_output.get("recommended_actions")):
        item = _safe_dict(value)
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            continue
        actions.append(
            AdvisorBriefActionItem(
                label=label.strip(),
                target_mode=_infer_target_mode_from_text(label),
                route=route,
            )
        )
    return actions


def _parse_ai_narrative_item(
    *,
    value: Any,
    route: str,
    default_mode: str,
) -> AdvisorBriefNarrativeItem | None:
    item = _safe_dict(value)
    headline = item.get("headline")
    detail = item.get("detail")
    if not isinstance(headline, str) or not headline.strip():
        return None
    if not isinstance(detail, str) or not detail.strip():
        return None
    tone = _normalize_narrative_tone(item.get("tone"))
    evidence_refs = [
        ref
        for ref in (
            _parse_ai_evidence_ref(value=ref_value, route=route, default_mode=default_mode)
            for ref_value in _safe_list(item.get("evidence_refs"))
        )
        if ref is not None
    ]
    if not evidence_refs:
        evidence_refs = [
            AdvisorBriefEvidenceRef(
                metric_label="Advisor Brief",
                metric_value="Source-Grounded",
                source_surface="performance.advisor_brief",
                target_mode=default_mode,
                route=route,
            )
        ]
    return AdvisorBriefNarrativeItem(
        headline=headline.strip(),
        detail=detail.strip(),
        tone=tone,
        evidence_refs=evidence_refs,
    )


def _parse_ai_evidence_ref(
    *,
    value: Any,
    route: str,
    default_mode: str,
) -> AdvisorBriefEvidenceRef | None:
    item = _safe_dict(value)
    metric_label = item.get("metric_label")
    metric_value = item.get("metric_value")
    if not isinstance(metric_label, str) or not metric_label.strip():
        return None
    if not isinstance(metric_value, str) or not metric_value.strip():
        return None
    source_ref = _safe_str(item.get("source_ref")) or _safe_str(item.get("source_surface"))
    source_surface = (
        _infer_source_surface(source_ref) if source_ref else "performance.advisor_brief"
    )
    return AdvisorBriefEvidenceRef(
        metric_label=metric_label.strip(),
        metric_value=metric_value.strip(),
        source_surface=source_surface,
        target_mode=_infer_target_mode(source_surface=source_surface, default_mode=default_mode),
        route=route,
    )


def _normalize_narrative_tone(value: Any) -> AdvisorBriefTone:
    if value == AdvisorBriefTone.POSITIVE.value:
        return AdvisorBriefTone.POSITIVE
    if value == AdvisorBriefTone.WARNING.value:
        return AdvisorBriefTone.WARNING
    return AdvisorBriefTone.NEUTRAL


def _infer_target_mode(*, source_surface: str, default_mode: str) -> str:
    return "summary" if source_surface == "performance.return_path" else default_mode


def _infer_target_mode_from_text(label: str) -> str:
    normalized = label.strip().lower()
    if "return" in normalized:
        return "summary"
    return "analysis"


def _infer_source_surface(source_ref: str | None) -> str:
    if not source_ref:
        return "performance.advisor_brief"
    normalized = source_ref.lower()
    if "performance-summary" in normalized:
        return "performance.return_path"
    if "performance-details" in normalized or "contribution" in normalized:
        return "performance.contribution"
    if "benchmark" in normalized or "attribution" in normalized:
        return "performance.attribution"
    return "performance.advisor_brief"


def _build_source_talking_points(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> list[AdvisorBriefNarrativeItem]:
    points: list[AdvisorBriefNarrativeItem] = []
    if (
        selected_performance.portfolio_return_pct is not None
        or selected_performance.benchmark_return_pct is not None
        or selected_performance.active_return_pct is not None
    ):
        points.append(
            AdvisorBriefNarrativeItem(
                headline=(
                    f"Portfolio return is {_format_pct(selected_performance.portfolio_return_pct)} "
                    f"versus benchmark {_format_pct(selected_performance.benchmark_return_pct)}."
                ),
                detail=(
                    f"Active return is {_format_pct(selected_performance.active_return_pct)} "
                    f"for the selected {workspace.period} period."
                ),
                tone=(
                    AdvisorBriefTone.POSITIVE
                    if (selected_performance.active_return_pct or 0) >= 0
                    else AdvisorBriefTone.WARNING
                ),
                evidence_refs=[
                    _summary_evidence_ref(
                        label="Active Return",
                        value=_format_pct(selected_performance.active_return_pct),
                        portfolio_id=workspace.portfolio_id,
                        period=workspace.period,
                        basis=workspace.detail_basis,
                        benchmark_code=workspace.benchmark_code,
                    )
                ],
            )
        )

    top_position = _positive_position_contributors(contribution=workspace.contribution)[:1]
    if top_position:
        points.append(
            AdvisorBriefNarrativeItem(
                headline=(
                    f"Top contributor is "
                    f"{_normalize_position_label(top_position[0].position_id)}."
                ),
                detail=(
                    f"{_normalize_position_label(top_position[0].position_id)} contributed "
                    f"{_format_pct(top_position[0].contribution_pct)} with return "
                    f"{_format_pct(top_position[0].total_return_pct)}."
                ),
                tone=AdvisorBriefTone.POSITIVE,
                evidence_refs=[
                    _analysis_evidence_ref(
                        label="Top Contributor",
                        value=_normalize_position_label(top_position[0].position_id),
                        portfolio_id=workspace.portfolio_id,
                        period=workspace.period,
                        basis=workspace.detail_basis,
                        benchmark_code=workspace.benchmark_code,
                    )
                ],
            )
        )

    bottom_position = _negative_position_contributors(contribution=workspace.contribution)[:1]
    if bottom_position:
        points.append(
            AdvisorBriefNarrativeItem(
                headline=(
                    f"Top detractor is "
                    f"{_normalize_position_label(bottom_position[0].position_id)}."
                ),
                detail=(
                    f"{_normalize_position_label(bottom_position[0].position_id)} contributed "
                    f"{_format_pct(bottom_position[0].contribution_pct)} with return "
                    f"{_format_pct(bottom_position[0].total_return_pct)}."
                ),
                tone=AdvisorBriefTone.WARNING,
                evidence_refs=[
                    _analysis_evidence_ref(
                        label="Top Detractor",
                        value=_normalize_position_label(bottom_position[0].position_id),
                        portfolio_id=workspace.portfolio_id,
                        period=workspace.period,
                        basis=workspace.detail_basis,
                        benchmark_code=workspace.benchmark_code,
                    )
                ],
            )
        )

    return points


def _build_recommended_actions(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> list[AdvisorBriefActionItem]:
    return [
        AdvisorBriefActionItem(
            label="Open Return Path",
            target_mode="summary",
            route=_route_query(
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            ),
        ),
        AdvisorBriefActionItem(
            label="Open Contribution",
            target_mode="analysis",
            route=_route_query(
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            ),
        ),
        AdvisorBriefActionItem(
            label="Open Attribution",
            target_mode="analysis",
            route=_route_query(
                portfolio_id=workspace.portfolio_id,
                period=workspace.period,
                basis=workspace.detail_basis,
                benchmark_code=workspace.benchmark_code,
            ),
        ),
    ]


def _build_risks_and_exceptions(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability: list[AdvisorBriefSupportabilityItem],
) -> list[AdvisorBriefNarrativeItem]:
    risks: list[AdvisorBriefNarrativeItem] = []
    for item in supportability:
        if item.tone not in {"warn", "danger"}:
            continue
        if item.label == "Advisor Brief":
            continue
        risks.append(
            AdvisorBriefNarrativeItem(
                headline=f"{item.label} is {item.value.lower()}.",
                detail=item.reason or "Source detail is not fully available for this selection.",
                tone=AdvisorBriefTone.WARNING,
                evidence_refs=[
                    AdvisorBriefEvidenceRef(
                        metric_label=item.label,
                        metric_value=item.value,
                        source_surface=f"performance.{item.label.lower().replace(' ', '_')}",
                        target_mode="analysis"
                        if item.label in {"Contribution", "Attribution"}
                        else "summary",
                        route=_route_query(
                            portfolio_id=workspace.portfolio_id,
                            period=workspace.period,
                            basis=workspace.detail_basis,
                            benchmark_code=workspace.benchmark_code,
                        ),
                    )
                ],
            )
        )
    return risks


def _build_source_metrics(
    *,
    workspace: PerformanceWorkspaceResponse,
    selected_performance: PerformanceComparativeSummary,
) -> list[AdvisorBriefSourceMetric]:
    route = _route_query(
        portfolio_id=workspace.portfolio_id,
        period=workspace.period,
        basis=workspace.detail_basis,
        benchmark_code=workspace.benchmark_code,
    )
    return [
        AdvisorBriefSourceMetric(
            label="Portfolio Return",
            value=_format_pct(selected_performance.portfolio_return_pct),
            support_label=f"{workspace.period} {workspace.detail_basis}",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        AdvisorBriefSourceMetric(
            label="Benchmark Return",
            value=_format_pct(selected_performance.benchmark_return_pct),
            support_label=workspace.benchmark_code or "Unassigned",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        AdvisorBriefSourceMetric(
            label="Active Return",
            value=_format_pct(selected_performance.active_return_pct),
            support_label=f"{workspace.report_start_date} to {workspace.report_end_date}",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.benchmark_comparison.state,
        ),
        AdvisorBriefSourceMetric(
            label="Net Flow",
            value=_format_currency(selected_performance.net_cash_flow),
            support_label=workspace.portfolio.base_currency or "Portfolio currency",
            target_mode="summary",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
        AdvisorBriefSourceMetric(
            label="Ending MV",
            value=_format_currency(selected_performance.end_market_value),
            support_label=workspace.report_end_date,
            target_mode="summary",
            route=route,
            state=workspace.capabilities.summary_kpis.state,
        ),
    ]


def _build_supportability(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> list[AdvisorBriefSupportabilityItem]:
    items = [
        _to_supportability_item("Portfolio", workspace.capabilities.summary_kpis.state, None),
        _to_supportability_item(
            "Return History",
            workspace.capabilities.return_path.state,
            workspace.capabilities.return_path.reason,
        ),
        _to_supportability_item(
            "Contribution",
            workspace.capabilities.contribution_detail.state,
            workspace.capabilities.contribution_detail.reason,
        ),
        _to_supportability_item(
            "Attribution",
            workspace.capabilities.attribution_detail.state,
            workspace.capabilities.attribution_detail.reason,
        ),
    ]
    advisor_brief_value = "Ready"
    advisor_brief_tone = "success"
    if any(item.tone == "danger" for item in items[:2]):
        advisor_brief_value = "Unavailable"
        advisor_brief_tone = "danger"
    elif any(item.tone in {"warn", "danger"} for item in items):
        advisor_brief_value = "Partial"
        advisor_brief_tone = "warn"

    items.append(
        AdvisorBriefSupportabilityItem(
            label="Advisor Brief",
            value=advisor_brief_value,
            tone=advisor_brief_tone,
            reason=None,
        )
    )
    return items


def _to_supportability_item(
    label: str,
    state: str,
    reason: str | None,
) -> AdvisorBriefSupportabilityItem:
    normalized_state = state.strip().lower()
    if normalized_state in {"ready", "supported"}:
        return AdvisorBriefSupportabilityItem(
            label=label,
            value="Ready",
            tone="success",
            reason=reason,
        )
    if normalized_state == "partial":
        return AdvisorBriefSupportabilityItem(
            label=label,
            value="Partial",
            tone="warn",
            reason=reason,
        )
    return AdvisorBriefSupportabilityItem(
        label=label,
        value="Unavailable",
        tone="danger",
        reason=reason,
    )


def _resolve_status(
    *,
    workspace: PerformanceWorkspaceResponse,
    supportability: list[AdvisorBriefSupportabilityItem],
) -> AdvisorBriefStatus:
    if workspace.capabilities.summary_kpis.state == "unavailable":
        return AdvisorBriefStatus.UNAVAILABLE
    if any(item.tone in {"warn", "danger"} for item in supportability):
        return AdvisorBriefStatus.PARTIAL
    return AdvisorBriefStatus.READY


def _positive_position_contributors(
    *,
    contribution: ContributionSummaryView | None,
) -> list[ContributionPositionView]:
    if not contribution:
        return []
    return sorted(
        [row for row in contribution.position_rows if row.contribution_pct > 0],
        key=lambda row: row.contribution_pct,
        reverse=True,
    )


def _negative_position_contributors(
    *,
    contribution: ContributionSummaryView | None,
) -> list[ContributionPositionView]:
    if not contribution:
        return []
    return sorted(
        [row for row in contribution.position_rows if row.contribution_pct < 0],
        key=lambda row: row.contribution_pct,
    )


def _top_attribution_effects(
    *,
    attribution: AttributionSummaryView | None,
) -> list[dict[str, Any]]:
    if not attribution:
        return []
    rows = [
        row
        for level in attribution.levels
        for row in level.rows
        if row.total_effect_pct is not None
    ]
    return [
        {
            "segment_label": row.key_label,
            "total_effect_pct": row.total_effect_pct,
            "allocation_pct": row.allocation_pct,
            "selection_pct": row.selection_pct,
            "interaction_pct": row.interaction_pct,
            "portfolio_weight_avg_pct": row.portfolio_weight_avg_pct,
            "benchmark_weight_avg_pct": row.benchmark_weight_avg_pct,
            "portfolio_return_pct": row.portfolio_return_pct,
            "benchmark_return_pct": row.benchmark_return_pct,
        }
        for row in sorted(
            rows,
            key=lambda row: abs(row.total_effect_pct),
            reverse=True,
        )[:5]
    ]


def _summary_evidence_ref(
    *,
    label: str,
    value: str,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
) -> AdvisorBriefEvidenceRef:
    return AdvisorBriefEvidenceRef(
        metric_label=label,
        metric_value=value,
        source_surface="performance.return_path",
        target_mode="summary",
        route=_route_query(
            portfolio_id=portfolio_id,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
        ),
    )


def _analysis_evidence_ref(
    *,
    label: str,
    value: str,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
) -> AdvisorBriefEvidenceRef:
    return AdvisorBriefEvidenceRef(
        metric_label=label,
        metric_value=value,
        source_surface="performance.contribution",
        target_mode="analysis",
        route=_route_query(
            portfolio_id=portfolio_id,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
        ),
    )


def _route_query(
    *,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
) -> str:
    route = (
        f"/performance?portfolioId={portfolio_id}&period={period}&detailBasis={basis}"
    )
    if benchmark_code:
        route += f"&benchmark={benchmark_code}"
    return route


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def _format_currency(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_error_detail(payload: dict[str, Any]) -> str:
    detail = payload.get("detail")
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return "lotus-ai task execution did not return a completed advisor brief."


def _normalize_position_label(position_id: str) -> str:
    display_label = position_id.rsplit(":", 1)[-1].strip()
    for prefix in ("FO_EQ_", "FO_FI_", "FO_CASH_", "FO_ALT_", "FO_FX_"):
        if display_label.startswith(prefix):
            display_label = display_label[len(prefix):]
            break
    return display_label.replace("_", " ").strip() or position_id


def _portfolio_display_label(*, workspace: PerformanceWorkspaceResponse) -> str:
    return _normalize_position_label(workspace.portfolio.portfolio_id)


def _benchmark_display_label(*, workspace: PerformanceWorkspaceResponse) -> str | None:
    if not workspace.benchmark_code:
        return None
    for option in workspace.benchmark_options:
        if option.benchmark_code == workspace.benchmark_code:
            return option.benchmark_name.strip() or workspace.benchmark_code
    return workspace.benchmark_code
