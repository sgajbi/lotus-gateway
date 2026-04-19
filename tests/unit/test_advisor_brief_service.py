import pytest

from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionRowView,
    AttributionSummaryView,
    ContributionPositionView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceBenchmarkOptionView,
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
from app.middleware.server_timing import (
    format_server_timing_header,
    reset_server_timing_metrics,
    restore_server_timing_metrics,
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
                "message": (
                    "AI summary: portfolio return exceeded benchmark over the selected period."
                ),
                "structured_output": {
                    "grounded_summary": (
                        "AI summary: portfolio return exceeded benchmark over the selected period."
                    ),
                    "talking_points": [
                        {
                            "headline": "AI-generated active-return summary.",
                            "detail": "Use Return Path to explain the benchmark gap.",
                            "tone": "warning",
                            "evidence_refs": [
                                {
                                    "metric_label": "Active Return",
                                    "metric_value": "-6.68%",
                                    "source_ref": (
                                        "lotus-gateway:workbench:PF_1001:performance-summary:YTD"
                                    ),
                                }
                            ],
                        }
                    ],
                    "recommended_actions": [
                        {
                            "label": "Review Return Path",
                            "detail": "Check period and flow context.",
                            "evidence_refs": [],
                        }
                    ],
                    "risks_and_exceptions": [
                        {
                            "headline": "Attribution evidence is partial.",
                            "detail": "Keep the narrative constrained to available source metrics.",
                            "tone": "warning",
                            "evidence_refs": [
                                {
                                    "metric_label": "Attribution",
                                    "metric_value": "Partial",
                                    "source_ref": (
                                        "lotus-gateway:workbench:PF_1001:performance-details:YTD"
                                    ),
                                }
                            ],
                        }
                    ],
                },
            },
            "audit": {
                "request_id": "req-1",
                "task_id": "explain.v1",
                "provider_mode": "openai",
                "provider_id": "text.openai",
                "adapter_kind": "OPENAI_LIVE",
                "model_id": "gpt-5.4",
                "stubbed": False,
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
        self.consumer_view_status_code = 200
        self.consumer_view_payload = {
            "run_id": "packrun_advisor_brief_req-1",
            "review": {
                "allowed_actions": ["ACCEPT", "REJECT", "REVISE", "SUPERSEDE", "ABANDON"],
            },
            "lineage": {"workflow_authority_owner": "lotus-gateway"},
        }
        self.operator_profile_status_code = 200
        self.operator_profile_payload = {
            "run_id": "packrun_advisor_brief_req-1",
            "runtime_state": "COMPLETED",
            "review_state": "AWAITING_REVIEW",
            "supportability_status": "ACTION_REQUIRED",
            "review_pending": True,
            "superseded": False,
            "current_summary_note": (
                "Run completed but still requires bounded human review before downstream use."
            ),
            "replacement_run_id": None,
            "findings": [
                {
                    "finding_id": "review_pending",
                    "severity": "ACTION_REQUIRED",
                    "summary": "Run is awaiting review.",
                }
            ],
        }
        self.execute_calls: list[dict[str, object]] = []
        self.consumer_view_calls: list[dict[str, object]] = []
        self.operator_profile_calls: list[dict[str, object]] = []

    async def execute_task(self, **kwargs):
        self.execute_calls.append(kwargs)
        return self.status_code, self.payload

    async def get_workflow_pack_run_consumer_view(self, **kwargs):
        self.consumer_view_calls.append(kwargs)
        return self.consumer_view_status_code, self.consumer_view_payload

    async def get_workflow_pack_run_operator_profile(self, **kwargs):
        self.operator_profile_calls.append(kwargs)
        return self.operator_profile_status_code, self.operator_profile_payload


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
    assert response.talking_points[0].headline == "AI-generated active-return summary."
    assert response.talking_points[0].evidence_refs[0].source_surface == "performance.return_path"
    assert response.recommended_actions[0].label == "Review Return Path"
    assert response.risks_and_exceptions[0].headline == "Attribution evidence is partial."
    assert response.risks_and_exceptions[0].evidence_refs[0].target_mode == "analysis"
    assert response.source_metrics[0].label == "Portfolio Return"
    assert response.source_metrics[0].route == (
        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
        "&benchmark=BMK_GLOBAL_BALANCED_60_40"
    )
    assert response.ai_audit["request_id"] == "req-1"
    assert response.ai_audit["provider_mode"] == "openai"
    assert response.ai_audit["provider_id"] == "text.openai"
    assert response.ai_audit["adapter_kind"] == "OPENAI_LIVE"
    assert response.ai_audit["model_id"] == "gpt-5.4"
    assert response.ai_audit["stubbed"] is False
    assert response.ai_evidence["descriptors"][0]["evidence_type"] == "source_fact_bundle"
    assert response.workflow_pack_run is not None
    assert response.workflow_pack_run.run_id == "packrun_advisor_brief_req-1"
    assert response.workflow_pack_run.review_state == "AWAITING_REVIEW"
    assert response.workflow_pack_run.workflow_authority_owner == "lotus-gateway"
    assert response.workflow_pack_run.findings[0].finding_id == "review_pending"
    assert workspace_service.calls[0]["portfolio_id"] == "PF_1001"
    assert ai_client.execute_calls[0]["task_id"] == "explain.v1"
    assert ai_client.execute_calls[0]["expected_output_label"] == "EXPLANATION_ONLY"
    assert ai_client.execute_calls[0]["context_payload"]["portfolio"]["portfolio_id"] == "PF_1001"
    assert ai_client.execute_calls[0]["context_payload"]["portfolio"]["display_label"] == "PF 1001"
    assert set(ai_client.execute_calls[0]["context_payload"]["portfolio"].keys()) == {
        "portfolio_id",
        "display_label",
        "base_currency",
        "booking_center_code",
        "client_id",
    }
    assert ai_client.execute_calls[0]["context_payload"]["benchmark"]["benchmark_name"] == (
        "Private Banking Global Balanced 60/40"
    )
    top_position = ai_client.execute_calls[0]["context_payload"]["contribution"]["top_positions"][0]
    assert set(top_position.keys()) == {
        "display_label",
        "contribution_pct",
        "weight_avg_pct",
        "total_return_pct",
        "local_contribution_pct",
        "fx_contribution_pct",
    }
    assert top_position["display_label"] == "AAPL US"
    top_effect = ai_client.execute_calls[0]["context_payload"]["attribution"]["top_effects"][0]
    assert set(top_effect.keys()) == {
        "segment_label",
        "total_effect_pct",
        "allocation_pct",
        "selection_pct",
        "interaction_pct",
        "portfolio_weight_avg_pct",
        "benchmark_weight_avg_pct",
        "portfolio_return_pct",
        "benchmark_return_pct",
    }
    assert ai_client.execute_calls[0]["source_refs"] == [
        "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
        "lotus-gateway:workbench:PF_1001:performance-details:YTD",
        "lotus-performance:benchmark:PF_1001:BMK_GLOBAL_BALANCED_60_40:YTD",
    ]
    assert ai_client.consumer_view_calls == [
        {"run_id": "packrun_advisor_brief_req-1", "correlation_id": "corr-1"}
    ]
    assert ai_client.operator_profile_calls == [
        {"run_id": "packrun_advisor_brief_req-1", "correlation_id": "corr-1"}
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_marks_partial_for_partial_sources_or_ai():
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
    assert response.ai_audit["provider_id"] is None
    assert response.ai_audit["adapter_kind"] is None
    assert response.ai_audit["model_id"] is None
    assert response.ai_audit["stubbed"] is True
    assert response.ai_audit["detail"] == "lotus-ai paused"
    assert response.workflow_pack_run is None
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


@pytest.mark.asyncio
async def test_advisor_brief_service_reuses_cached_response_for_identical_request():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
        cache_ttl_seconds=60.0,
    )

    first = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-1",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )
    second = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-2",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert first.summary == second.summary
    assert len(workspace_service.calls) == 1
    assert len(ai_client.execute_calls) == 1
    assert len(ai_client.consumer_view_calls) == 1
    assert len(ai_client.operator_profile_calls) == 1


@pytest.mark.asyncio
async def test_advisor_brief_service_cache_key_changes_when_request_shape_changes():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
        cache_ttl_seconds=60.0,
    )

    await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-net",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )
    await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-gross",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="GROSS",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert len(workspace_service.calls) == 2
    assert len(ai_client.execute_calls) == 2
    assert len(ai_client.consumer_view_calls) == 2
    assert len(ai_client.operator_profile_calls) == 2


@pytest.mark.asyncio
async def test_advisor_brief_service_treats_supported_capabilities_as_ready():
    workspace = _build_workspace(
        benchmark_state="supported",
        contribution_state="supported",
        attribution_state="supported",
    )
    workspace.capabilities.summary_kpis.state = "supported"
    workspace.capabilities.return_path.state = "supported"
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(workspace),
        lotus_ai_client=_StubLotusAiClient(),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-supported",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "ready"
    assert [item.value for item in response.supportability] == [
        "Ready",
        "Ready",
        "Ready",
        "Ready",
        "Ready",
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_normalizes_raw_position_ids_in_fallback_copy():
    workspace = _build_workspace()
    workspace.contribution.position_rows = [
        ContributionPositionView(
            position_id="PF_1001:FO_EQ_AAPL_US",
            contribution_pct=0.30,
            weight_avg_pct=7.37,
            total_return_pct=4.31,
        ),
        ContributionPositionView(
            position_id="PF_1001:FO_CASH_USD_BOOK_OPERATING",
            contribution_pct=-0.06,
            weight_avg_pct=9.24,
            total_return_pct=0.00,
        ),
    ]
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(workspace),
        lotus_ai_client=_StubLotusAiClient(
            payload={
                "status": "COMPLETED",
                "task_id": "explain.v1",
                "result": {
                    "message": "Fallback summary only.",
                    "structured_output": {
                        "grounded_summary": "Fallback summary only.",
                        "talking_points": [],
                        "recommended_actions": [],
                        "risks_and_exceptions": [],
                    },
                },
                "audit": {},
                "evidence": {"descriptors": []},
            }
        ),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-raw-position-id",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert "PF_1001:" not in response.talking_points[1].headline
    assert response.talking_points[1].headline == "Top contributor is AAPL US."
    assert response.talking_points[2].headline == "Top detractor is USD BOOK OPERATING."
    assert response.talking_points[2].detail == (
        "USD BOOK OPERATING contributed -0.06% with return 0.00%."
    )


@pytest.mark.asyncio
async def test_advisor_brief_service_omits_workflow_pack_run_when_surfaces_unavailable():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    ai_client.consumer_view_status_code = 404
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-run-missing",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_GLOBAL_BALANCED_60_40",
    )

    assert response.workflow_pack_run is None
    assert ai_client.consumer_view_calls == [
        {"run_id": "packrun_advisor_brief_req-1", "correlation_id": "corr-run-missing"}
    ]
    assert ai_client.operator_profile_calls == []


@pytest.mark.asyncio
async def test_advisor_brief_service_records_source_and_ai_server_timing_spans():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )
    token = reset_server_timing_metrics()

    try:
        await service.get_performance_advisor_brief(
            portfolio_id="PF_1001",
            correlation_id="corr-1",
            period="YTD",
            chart_frequency="monthly",
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            detail_basis="NET",
            benchmark_code="BMK_GLOBAL_BALANCED_60_40",
        )

        server_timing = format_server_timing_header(1.0)
    finally:
        restore_server_timing_metrics(token)

    assert "perf-advisor-brief-source;dur=" in server_timing
    assert "perf-advisor-brief-ai;dur=" in server_timing


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
        benchmark_options=[
            PerformanceBenchmarkOptionView(
                benchmark_code="BMK_GLOBAL_BALANCED_60_40",
                benchmark_name="Private Banking Global Balanced 60/40",
                benchmark_currency="USD",
            )
        ],
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
