from dataclasses import dataclass, replace
from datetime import date

import pytest

from app.contracts.performance_workspace import (
    PerformanceBenchmarkOptionView,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
)
from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.services.performance_workspace_capabilities import build_workspace_capabilities
from app.services.performance_workspace_response import (
    WorkspaceResponseComponents,
    WorkspaceSummaryViews,
    assemble_performance_workspace_response,
    workspace_response_context_fields,
)
from app.services.performance_workspace_summary import ParsedWorkspaceSummary


@dataclass(frozen=True)
class _WorkspaceContext:
    overview: WorkbenchOverviewResponse
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]
    report_end_date: str
    report_start_date: date
    effective_period: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    requested_chart_frequency_supported: bool
    requested_contribution_dimension_supported: bool
    requested_attribution_dimension_supported: bool
    segment: str
    requested_as_of_date: str | None = None
    requested_reporting_currency: str | None = None
    reporting_currency: str = "USD"


def _context() -> _WorkspaceContext:
    return _WorkspaceContext(
        overview=WorkbenchOverviewResponse(
            correlation_id="corr-workspace-source",
            contract_version="v-test",
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
        ),
        warnings=["FOUNDATION_WARNING"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="lotus-performance",
                error_code="ATTRIBUTION_PARTIAL",
                detail="Attribution detail is partially available.",
            )
        ],
        report_end_date="2026-03-27",
        report_start_date=date(2026, 1, 1),
        effective_period="YTD",
        chart_frequency="MONTHLY",
        contribution_dimension="asset_class",
        attribution_dimension="sector",
        detail_basis="NET",
        requested_chart_frequency_supported=False,
        requested_contribution_dimension_supported=True,
        requested_attribution_dimension_supported=False,
        segment="2026-01-01:2026-03-27",
    )


def _summary_views() -> WorkspaceSummaryViews:
    parsed_summary = ParsedWorkspaceSummary(
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            portfolio_return_pct=5.12,
            benchmark_return_pct=4.9,
            active_return_pct=0.22,
        ),
        gross_performance=PerformanceComparativeSummary(
            metric_basis="GROSS",
            portfolio_return_pct=5.2,
        ),
        net_chart=[
            PerformanceChartPoint(
                label="2026-03",
                frequency="MONTHLY",
                portfolio_return_pct=1.2,
            )
        ],
        gross_chart=[],
        money_weighted_return=None,
        contribution=None,
        attribution=None,
        resolved_benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )
    return WorkspaceSummaryViews(
        workspace_summary_result=(
            200,
            {
                "calculation_id": "calc-workspace-summary",
                "results_by_period": {
                    "YTD": {"portfolio_twr": {"net": {"summary": {"period_return": {"base": 1.0}}}}}
                },
            },
        ),
        parsed_summary=parsed_summary,
        contribution=None,
        attribution=None,
        contribution_detail_result=None,
        attribution_detail_result=None,
    )


def test_workspace_response_context_fields_preserve_supported_flags() -> None:
    fields = workspace_response_context_fields(_context())

    assert fields.contract_version == "v-test"
    assert fields.as_of_date == "2026-03-27"
    assert fields.period == "YTD"
    assert fields.report_start_date == "2026-01-01"
    assert fields.report_end_date == "2026-03-27"
    assert fields.requested_chart_frequency_supported is False
    assert fields.requested_contribution_dimension_supported is True
    assert fields.requested_attribution_dimension_supported is False
    assert fields.segment == "2026-01-01:2026-03-27"


@pytest.mark.parametrize(
    ("result", "expected_currency", "expected_state"),
    [
        (
            (
                200,
                {
                    "results_by_period": {
                        "YTD": {
                            "portfolio_twr": {"net": {"summary": {"period_return": {"base": 1.0}}}}
                        }
                    }
                },
            ),
            "SGD",
            "accepted_unverified",
        ),
        (
            (200, {"results_by_period": {"YTD": []}}),
            "USD",
            "unavailable",
        ),
        (
            (
                200,
                {
                    "results_by_period": {
                        "YTD": {
                            "portfolio_twr": {
                                "net": {"summary": {"period_return": {"base": "not-a-number"}}}
                            }
                        }
                    }
                },
            ),
            "USD",
            "unavailable",
        ),
        (
            (
                200,
                {
                    "results_by_period": {
                        "YTD": {
                            "portfolio_twr": {"net": {"summary": {"period_return": {"local": 1.0}}}}
                        }
                    }
                },
            ),
            "USD",
            "unavailable",
        ),
        (
            (200, {"results_by_period": {"YTD": {"error": "invalid summary"}}}),
            "USD",
            "unavailable",
        ),
        (
            (
                200,
                {
                    "results_by_period": {
                        "YTD": {"portfolio_twr": {"net": {"summary": {"period_return": {}}}}}
                    }
                },
            ),
            "USD",
            "unavailable",
        ),
        (
            (
                422,
                {
                    "error_code": "VALIDATION_ERROR",
                    "validation_errors": [{"loc": ["body", "report_ccy"]}],
                },
            ),
            "USD",
            "rejected",
        ),
        (
            (
                422,
                {
                    "error_code": "VALIDATION_ERROR",
                    "validation_errors": [{"loc": ["body", "as_of_date"]}],
                },
            ),
            "USD",
            "unavailable",
        ),
        ((503, {"detail": "upstream unavailable"}), "USD", "unavailable"),
        (TimeoutError("summary timeout"), "USD", "unavailable"),
    ],
)
def test_workspace_response_context_fields_classify_currency_state(
    result: tuple[int, dict[str, object]] | BaseException,
    expected_currency: str,
    expected_state: str,
) -> None:
    fields = workspace_response_context_fields(
        replace(
            _context(),
            requested_reporting_currency="SGD",
            reporting_currency="SGD",
        ),
        workspace_summary_result=result,
    )

    assert fields.effective_reporting_currency == expected_currency
    assert fields.reporting_currency_state == expected_state


def test_workspace_response_context_fields_do_not_text_match_currency_rejection() -> None:
    context = replace(
        _context(),
        requested_reporting_currency="SGD",
        reporting_currency="SGD",
    )
    fields = workspace_response_context_fields(
        context,
        workspace_summary_result=(422, {"detail": "unsupported reporting currency"}),
    )

    assert fields.effective_reporting_currency == "USD"
    assert fields.reporting_currency_state == "unavailable"


def test_assemble_performance_workspace_response_preserves_context_and_components() -> None:
    context = _context()
    summary_views = _summary_views()
    capabilities = build_workspace_capabilities(
        benchmark_code=summary_views.resolved_benchmark_code,
        net_performance=summary_views.net_performance,
        net_chart=summary_views.net_chart,
        contribution=summary_views.contribution,
        attribution=summary_views.attribution,
        evidence_view=None,
    )

    response = assemble_performance_workspace_response(
        portfolio_id="PF_1001",
        correlation_id="corr-performance-workspace",
        context=context,
        summary_views=summary_views,
        response_components=WorkspaceResponseComponents(
            benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
            benchmark_options=[
                PerformanceBenchmarkOptionView(
                    benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
                    benchmark_name="Global Balanced 60/40",
                    is_assigned=True,
                )
            ],
            evidence_view=None,
            capabilities=capabilities,
        ),
    )

    assert response.correlation_id == "corr-performance-workspace"
    assert response.contract_version == "v-test"
    assert response.portfolio_id == "PF_1001"
    assert response.report_start_date == "2026-01-01"
    assert response.reporting_currency_state == "accepted_unverified"
    assert response.requested_chart_frequency_supported is False
    assert response.requested_attribution_dimension_supported is False
    assert response.benchmark_code == "BMK_PB_GLOBAL_BALANCED_60_40"
    assert response.benchmark_options[0].is_assigned is True
    assert response.capabilities.benchmark_comparison.state == "supported"
    assert response.portfolio.client_id == "CIF_1001"
    assert response.overview.position_count == 3
    assert response.net_performance.portfolio_return_pct == 5.12
    assert response.net_chart[0].label == "2026-03"
    assert response.warnings == ["FOUNDATION_WARNING"]
    assert response.partial_failures[0].error_code == "ATTRIBUTION_PARTIAL"
