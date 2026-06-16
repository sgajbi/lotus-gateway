from datetime import date

from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.performance_workspace_context import (
    WorkspaceBenchmarkContext,
    WorkspaceOverviewState,
    WorkspaceReportWindow,
    assemble_attribution_trend_request_context,
    assemble_horizon_comparison_request_context,
    assemble_workspace_request_context,
    build_attribution_trend_dimension_context,
    build_horizon_chart_frequency_context,
    build_workspace_dimension_context,
)


def _overview_state() -> WorkspaceOverviewState:
    return WorkspaceOverviewState(
        overview=WorkbenchOverviewResponse(
            correlation_id="corr-performance",
            contract_version="v1",
            as_of_date="2026-03-27",
            portfolio=WorkbenchPortfolioSummary(
                portfolio_id="PF_1001",
                client_id="CIF_1001",
                base_currency="USD",
                booking_center_code="SG",
            ),
            overview=WorkbenchOverviewSummary(
                market_value_base=508_870.0,
                cash_weight_pct=46.25,
                position_count=3,
            ),
            warnings=["FOUNDATION_WARNING"],
            partial_failures=[
                WorkbenchPartialFailure(
                    source_service="lotus-core",
                    error_code="STALE_REPORTING",
                    detail="reporting snapshot is older than expected",
                )
            ],
        ),
        warnings=["FOUNDATION_WARNING"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="lotus-core",
                error_code="STALE_REPORTING",
                detail="reporting snapshot is older than expected",
            )
        ],
    )


def _report_window() -> WorkspaceReportWindow:
    return WorkspaceReportWindow(
        report_end_date="2026-03-27",
        report_start_date=date(2026, 1, 1),
        effective_period="YTD",
    )


def _benchmark_context() -> WorkspaceBenchmarkContext:
    return WorkspaceBenchmarkContext(
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        benchmark_catalog_result=(200, {"records": []}),
    )


def test_build_workspace_dimension_context_normalizes_unsupported_controls() -> None:
    warnings: list[str] = []

    context = build_workspace_dimension_context(
        chart_frequency="weekly",
        contribution_dimension="Region",
        attribution_dimension="issuer",
        warnings=warnings,
    )

    assert context.chart_frequency == "monthly"
    assert context.contribution_dimension == "asset_class"
    assert context.attribution_dimension == "asset_class"
    assert context.segment == "asset_class"
    assert context.requested_chart_frequency_supported is False
    assert context.requested_contribution_dimension_supported is False
    assert context.requested_attribution_dimension_supported is False
    assert warnings == [
        "PERFORMANCE_CHART_FREQUENCY_NORMALIZED",
        "PERFORMANCE_CONTRIBUTION_DIMENSION_NORMALIZED",
        "PERFORMANCE_ATTRIBUTION_DIMENSION_NORMALIZED",
    ]


def test_build_workspace_dimension_context_records_shared_segment_alignment() -> None:
    warnings: list[str] = []

    context = build_workspace_dimension_context(
        chart_frequency="monthly",
        contribution_dimension="sector",
        attribution_dimension="country",
        warnings=warnings,
    )

    assert context.contribution_dimension == "sector"
    assert context.attribution_dimension == "country"
    assert context.segment == "sector"
    assert context.requested_contribution_dimension_supported is True
    assert context.requested_attribution_dimension_supported is True
    assert warnings == ["PERFORMANCE_SEGMENTATION_ALIGNED_TO_SHARED_SOURCE_CONTRACT"]


def test_assemble_workspace_request_context_preserves_source_state() -> None:
    overview_state = _overview_state()
    dimension_context = build_workspace_dimension_context(
        chart_frequency="quarterly",
        contribution_dimension="sector",
        attribution_dimension="sector",
        warnings=overview_state.warnings,
    )

    context = assemble_workspace_request_context(
        overview_state=overview_state,
        report_window=_report_window(),
        dimension_context=dimension_context,
        detail_basis="NET",
        benchmark_context=_benchmark_context(),
    )

    assert context.overview.portfolio.portfolio_id == "PF_1001"
    assert context.report_start_date == date(2026, 1, 1)
    assert context.report_end_date == "2026-03-27"
    assert context.effective_period == "YTD"
    assert context.detail_basis == "NET"
    assert context.chart_frequency == "quarterly"
    assert context.segment == "sector"
    assert context.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert context.warnings == ["FOUNDATION_WARNING"]
    assert context.partial_failures[0].error_code == "STALE_REPORTING"


def test_build_horizon_chart_frequency_context_uses_horizon_warning_code() -> None:
    warnings: list[str] = []

    context = build_horizon_chart_frequency_context(
        chart_frequency="daily",
        warnings=warnings,
    )

    assert context.chart_frequency == "monthly"
    assert context.requested_chart_frequency_supported is False
    assert warnings == ["PERFORMANCE_HORIZON_CHART_FREQUENCY_NORMALIZED"]


def test_assemble_horizon_comparison_request_context_preserves_benchmark_catalog() -> None:
    overview_state = _overview_state()
    chart_frequency_context = build_horizon_chart_frequency_context(
        chart_frequency="monthly",
        warnings=overview_state.warnings,
    )

    context = assemble_horizon_comparison_request_context(
        overview_state=overview_state,
        report_window=_report_window(),
        chart_frequency_context=chart_frequency_context,
        benchmark_context=_benchmark_context(),
    )

    assert context.chart_frequency == "monthly"
    assert context.requested_chart_frequency_supported is True
    assert context.benchmark_catalog_result == (200, {"records": []})
    assert context.warnings == ["FOUNDATION_WARNING"]


def test_build_attribution_trend_dimension_context_uses_trend_warning_codes() -> None:
    warnings: list[str] = []

    context = build_attribution_trend_dimension_context(
        chart_frequency="weekly",
        attribution_dimension="issuer",
        warnings=warnings,
    )

    assert context.chart_frequency == "monthly"
    assert context.attribution_dimension == "asset_class"
    assert context.requested_chart_frequency_supported is False
    assert context.requested_attribution_dimension_supported is False
    assert warnings == [
        "PERFORMANCE_ATTRIBUTION_TREND_CHART_FREQUENCY_NORMALIZED",
        "PERFORMANCE_ATTRIBUTION_TREND_DIMENSION_NORMALIZED",
    ]


def test_assemble_attribution_trend_request_context_preserves_request_policy() -> None:
    overview_state = _overview_state()
    dimension_context = build_attribution_trend_dimension_context(
        chart_frequency="quarterly",
        attribution_dimension="sector",
        warnings=overview_state.warnings,
    )

    context = assemble_attribution_trend_request_context(
        overview_state=overview_state,
        report_window=_report_window(),
        dimension_context=dimension_context,
        benchmark_context=_benchmark_context(),
    )

    assert context.chart_frequency == "quarterly"
    assert context.attribution_dimension == "sector"
    assert context.requested_chart_frequency_supported is True
    assert context.requested_attribution_dimension_supported is True
    assert context.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert context.partial_failures[0].source_service == "lotus-core"
