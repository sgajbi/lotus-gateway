import pytest

from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionRowView,
    AttributionSummaryView,
    ContributionPositionView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceComparativeSummary,
    PerformanceModuleCapability,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceResponse,
)
from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.advisor_brief_service import AdvisorBriefService


class _StubPerformanceWorkspaceService:
    def __init__(self, workspace: PerformanceWorkspaceResponse):
        self.workspace = workspace
        self.calls: list[dict[str, object]] = []

    async def get_performance_workspace(self, **kwargs):
        self.calls.append(kwargs)
        return self.workspace


class _StubLotusAiClient:
    def __init__(self, *, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self.payload = payload or {
            "status": "COMPLETED",
            "task_id": "explain.v1",
            "result": {
                "message": "AI summary: portfolio return exceeded benchmark over the selected period.",
                "structured_output": {},
            },
            "audit": {
                "request_id": "req-1",
                "task_id": "explain.v1",
                "provider_mode": "stub",
            },
            "evidence": {
                "descriptors": [
                    {
                        "evidence_type": "source_fact_bundle",
                        "summary": "Grounded in Gateway performance workspace facts.",
                        "attributes": {"portfolio_id": "PF_1001"},
                    }
                ]
            },
        }
        self.calls: list[dict[str, object]] = []

    async def execute_task(self, **kwargs):
        self.calls.append(kwargs)
        return self.status_code, self.payload


@pytest.mark.asyncio
async def test_advisor_brief_service_returns_ai_summary_and_source_grounded_actions():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-1",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "ready"
    assert response.summary.startswith("AI summary:")
    assert response.source_metrics[0].label == "Portfolio Return"
    assert response.source_metrics[0].route == (
        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
        "&benchmark=BMK_GLOBAL_BALANCED_60_40"
    )
    assert response.talking_points[0].evidence_refs[0].source_surface == "performance.return_path"
    assert [action.label for action in response.recommended_actions] == [
        "Open Return Path",
        "Open Contribution",
        "Open Attribution",
    ]
    assert response.ai_audit["request_id"] == "req-1"
    assert response.ai_evidence["descriptors"][0]["evidence_type"] == "source_fact_bundle"
    assert workspace_service.calls[0]["portfolio_id"] == "PF_1001"
    assert ai_client.calls[0]["task_id"] == "explain.v1"
    assert ai_client.calls[0]["expected_output_label"] == "EXPLANATION_ONLY"
    assert ai_client.calls[0]["context_payload"]["portfolio"]["portfolio_id"] == "PF_1001"
    assert ai_client.calls[0]["source_refs"] == [
        "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
        "lotus-gateway:workbench:PF_1001:performance-details:YTD",
        "lotus-performance:benchmark:PF_1001:BMK_GLOBAL_BALANCED_60_40:YTD",
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_marks_partial_when_source_slices_or_ai_generation_are_partial():
    workspace = _build_workspace(
        contribution_state="partial",
        attribution_state="unavailable",
        benchmark_state="partial",
    )
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(workspace),
        lotus_ai_client=_StubLotusAiClient(status_code=503, payload={"detail": "lotus-ai paused"}),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-partial",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "partial"
    assert response.ai_audit["provider_mode"] == "unavailable"
    assert response.ai_audit["detail"] == "lotus-ai paused"
    assert [item.model_dump(mode="json") for item in response.supportability] == [
        {"label": "Portfolio", "value": "Ready", "tone": "success", "reason": None},
        {"label": "Return History", "value": "Ready", "tone": "success", "reason": None},
        {
            "label": "Contribution",
            "value": "Partial",
            "tone": "warn",
            "reason": "Contribution aggregate only.",
        },
        {
            "label": "Attribution",
            "value": "Unavailable",
            "tone": "danger",
            "reason": "Attribution unavailable.",
        },
        {"label": "Advisor Brief", "value": "Partial", "tone": "warn", "reason": None},
    ]
    assert [item.model_dump(mode="json") for item in response.risks_and_exceptions] == [
        {
            "headline": "Contribution is partial.",
            "detail": "Contribution aggregate only.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Contribution",
                    "metric_value": "Partial",
                    "source_surface": "performance.contribution",
                    "target_mode": "analysis",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
                        "&benchmark=BMK_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        },
        {
            "headline": "Attribution is unavailable.",
            "detail": "Attribution unavailable.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Attribution",
                    "metric_value": "Unavailable",
                    "source_surface": "performance.attribution",
                    "target_mode": "analysis",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
                        "&benchmark=BMK_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        },
        {
            "headline": "AI narrative generation is unavailable.",
            "detail": "Source-backed metrics remain available for manual review and client prep.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Advisor Brief",
                    "metric_value": "Unavailable",
                    "source_surface": "performance.return_path",
                    "target_mode": "summary",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
                        "&benchmark=BMK_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        },
    ]


def _build_workspace(
    *,
    benchmark_state: str = "ready",
    contribution_state: str = "ready",
    attribution_state: str = "ready",
) -> PerformanceWorkspaceResponse:
    return PerformanceWorkspaceResponse(
        correlation_id="corr-1",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date="2026-04-04",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-04-04",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        requested_chart_frequency_supported=True,
        requested_contribution_dimension_supported=True,
        requested_attribution_dimension_supported=True,
        segment="asset_class",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
        capabilities=PerformanceWorkspaceCapabilities(
            summary_kpis=PerformanceModuleCapability(state="ready"),
            return_path=PerformanceModuleCapability(state="ready"),
            benchmark_comparison=PerformanceModuleCapability(state=benchmark_state),
            multi_horizon_returns=PerformanceModuleCapability(state="ready"),
            contribution_ranking=PerformanceModuleCapability(state=contribution_state),
            attribution_detail=PerformanceModuleCapability(
                state=attribution_state,
                reason="Attribution unavailable." if attribution_state != "ready" else None,
            ),
            contribution_detail=PerformanceModuleCapability(
                state=contribution_state,
                reason="Contribution aggregate only." if contribution_state != "ready" else None,
            ),
            evidence=PerformanceModuleCapability(state="ready"),
        ),
        portfolio=WorkbenchPortfolioSummary(
            portfolio_id="PF_1001",
            client_id="CIF_1001",
            base_currency="USD",
            booking_center_code="SG",
        ),
        overview=WorkbenchOverviewSummary(
            market_value_base=1_087_461.0,
            cash_weight_pct=8.5,
            position_count=10,
        ),
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            portfolio_return_pct=1.25,
            benchmark_return_pct=7.93,
            active_return_pct=-6.68,
            benchmark_id="BMK_GLOBAL_BALANCED_60_40",
            end_market_value=1_087_461.0,
            net_cash_flow=14_725.0,
        ),
        gross_performance=PerformanceComparativeSummary(
            metric_basis="GROSS",
            portfolio_return_pct=1.45,
            benchmark_return_pct=7.93,
            active_return_pct=-6.48,
            benchmark_id="BMK_GLOBAL_BALANCED_60_40",
            end_market_value=1_087_461.0,
            net_cash_flow=14_725.0,
        ),
        money_weighted_return=MoneyWeightedReturnSummary(
            money_weighted_return_pct=1.23,
            method="XIRR",
            start_date="2026-01-01",
            end_date="2026-04-04",
        ),
        net_chart=[],
        gross_chart=[],
        contribution=ContributionSummaryView(
            metric_basis="NET",
            portfolio_contribution_pct=1.25,
            coverage_mv_pct=100.0,
            position_rows=[
                ContributionPositionView(
                    position_id="AAPL US",
                    contribution_pct=0.30,
                    weight_avg_pct=7.37,
                    total_return_pct=4.31,
                ),
                ContributionPositionView(
                    position_id="USD BOOK OPERATING",
                    contribution_pct=-0.06,
                    weight_avg_pct=9.24,
                    total_return_pct=0.00,
                ),
            ],
            levels=[],
        ),
        attribution=AttributionSummaryView(
            metric_basis="NET",
            model="BF",
            linking="Carino",
            benchmark_id="BMK_GLOBAL_BALANCED_60_40",
            active_return_pct=-6.68,
            sum_of_effects_pct=-6.67,
            residual_pct=-0.01,
            levels=[
                AttributionLevelView(
                    dimension="asset_class",
                    total_effect_pct=-3.2,
                    rows=[
                        AttributionRowView(
                            key_label="Equity",
                            portfolio_weight_avg_pct=62.0,
                            benchmark_weight_avg_pct=55.0,
                            portfolio_return_pct=4.0,
                            benchmark_return_pct=8.0,
                            allocation_pct=-1.1,
                            selection_pct=-2.0,
                            interaction_pct=-0.1,
                            total_effect_pct=-3.2,
                        )
                    ],
                )
            ],
        ),
        warnings=["FOUNDATION_WARNING"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="lotus-core",
                error_code="FOUNDATION_WARNING",
                detail="Foundation context has warnings.",
            )
        ],
    )
