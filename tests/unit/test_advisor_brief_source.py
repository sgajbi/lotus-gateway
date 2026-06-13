from app.contracts.advisor_brief import AdvisorBriefStatus, AdvisorBriefTone
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
from app.services.advisor_brief_source import (
    build_advisor_brief_ai_fact_bundle,
    build_advisor_brief_source_context,
    build_advisor_brief_source_metrics,
)


def test_build_advisor_brief_source_context_preserves_source_grounded_narrative() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=_build_workspace(attribution_state="partial"),
        detail_basis="NET",
    )

    assert source_context.status is AdvisorBriefStatus.PARTIAL
    assert source_context.source_refs == [
        "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
        "lotus-gateway:workbench:PF_1001:performance-details:YTD",
        ("lotus-performance:benchmark:PF_1001:BMK_PB_GLOBAL_BALANCED_60_40:YTD"),
    ]
    assert (
        source_context.summary == "YTD portfolio return for PF 1001 is 1.25% versus "
        "Private Banking Global Balanced 60/40 7.93%, with active return -6.68%."
    )
    assert [point.headline for point in source_context.talking_points] == [
        "Portfolio return is 1.25% versus benchmark 7.93%.",
        "Top contributor is AAPL US.",
        "Top detractor is USD BOOK OPERATING.",
    ]
    assert source_context.talking_points[0].tone is AdvisorBriefTone.WARNING
    assert source_context.talking_points[1].tone is AdvisorBriefTone.POSITIVE
    assert source_context.talking_points[2].tone is AdvisorBriefTone.WARNING
    assert [action.label for action in source_context.recommended_actions] == [
        "Open Return Path",
        "Open Contribution",
        "Open Attribution",
    ]
    assert [item.label for item in source_context.supportability] == [
        "Portfolio",
        "Return History",
        "Contribution",
        "Attribution",
        "Advisor Brief",
    ]
    assert source_context.supportability[-1].value == "Partial"
    assert source_context.risks_and_exceptions[0].headline == "Attribution is partial."


def test_build_advisor_brief_source_metrics_preserves_route_and_quantized_values() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=_build_workspace(),
        detail_basis="NET",
    )

    metrics = build_advisor_brief_source_metrics(source_context=source_context)

    assert [(metric.label, metric.value, metric.state) for metric in metrics] == [
        ("Portfolio Return", "1.25%", "ready"),
        ("Benchmark Return", "7.93%", "ready"),
        ("Active Return", "-6.68%", "ready"),
        ("Net Flow", "$14,725", "ready"),
        ("Ending MV", "$1,087,461", "ready"),
    ]
    assert {metric.route for metric in metrics} == {
        (
            "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
            "&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
        )
    }


def test_build_advisor_brief_ai_fact_bundle_preserves_source_fact_shape() -> None:
    source_context = build_advisor_brief_source_context(
        workspace=_build_workspace(),
        detail_basis="NET",
    )

    payload = build_advisor_brief_ai_fact_bundle(source_context=source_context)

    assert payload["portfolio"] == {
        "portfolio_id": "PF_1001",
        "display_label": "PF 1001",
        "base_currency": "USD",
        "booking_center_code": "SG",
        "client_id": "CIF_1001",
    }
    assert payload["benchmark"]["benchmark_name"] == "Private Banking Global Balanced 60/40"
    assert payload["performance"]["active_return_pct"] == -6.68
    assert payload["contribution"]["top_positions"][0]["display_label"] == "AAPL US"
    assert payload["contribution"]["bottom_positions"][0]["display_label"] == "USD BOOK OPERATING"
    assert payload["attribution"]["top_effects"] == [
        {
            "segment_label": "Equity",
            "total_effect_pct": -3.2,
            "allocation_pct": -1.1,
            "selection_pct": -2.0,
            "interaction_pct": -0.1,
            "portfolio_weight_avg_pct": 62.0,
            "benchmark_weight_avg_pct": 55.0,
            "portfolio_return_pct": 4.0,
            "benchmark_return_pct": 8.0,
        }
    ]
    assert payload["supportability"][-1]["value"] == "Ready"
    assert payload["warnings"] == ["FOUNDATION_WARNING"]
    assert payload["partial_failures"][0]["error_code"] == "FOUNDATION_WARNING"


def _build_workspace(*, attribution_state: str = "ready") -> PerformanceWorkspaceResponse:
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
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        benchmark_options=[
            PerformanceBenchmarkOptionView(
                benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
                benchmark_name="Private Banking Global Balanced 60/40",
                benchmark_currency="USD",
            )
        ],
        capabilities=PerformanceWorkspaceCapabilities(
            summary_kpis=PerformanceModuleCapability(state="ready"),
            return_path=PerformanceModuleCapability(state="ready"),
            benchmark_comparison=PerformanceModuleCapability(state="ready"),
            multi_horizon_returns=PerformanceModuleCapability(state="ready"),
            contribution_ranking=PerformanceModuleCapability(state="ready"),
            attribution_detail=PerformanceModuleCapability(
                state=attribution_state,
                reason="Attribution unavailable." if attribution_state != "ready" else None,
            ),
            contribution_detail=PerformanceModuleCapability(state="ready"),
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
            benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
            end_market_value=1_087_461.0,
            net_cash_flow=14_725.0,
        ),
        gross_performance=PerformanceComparativeSummary(
            metric_basis="GROSS",
            portfolio_return_pct=1.45,
            benchmark_return_pct=7.93,
            active_return_pct=-6.48,
            benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
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
            benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
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
