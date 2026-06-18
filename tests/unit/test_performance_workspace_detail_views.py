from app.contracts.performance_workspace import PerformanceComparativeSummary
from app.services.performance_workspace_detail_views import (
    build_summary_workspace_detail_views,
    should_fetch_independent_detail_views,
    workspace_summary_has_return_payload,
)
from app.services.performance_workspace_summary import ParsedWorkspaceSummary


def _parsed_workspace_summary(
    *,
    portfolio_return_pct: float | None = None,
) -> ParsedWorkspaceSummary:
    return ParsedWorkspaceSummary(
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            portfolio_return_pct=portfolio_return_pct,
        ),
        gross_performance=PerformanceComparativeSummary(metric_basis="GROSS"),
        net_chart=[],
        gross_chart=[],
        money_weighted_return=None,
        contribution=None,
        attribution=None,
        resolved_benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )


def test_workspace_summary_has_return_payload_uses_supported_return_families() -> None:
    assert workspace_summary_has_return_payload(_parsed_workspace_summary(portfolio_return_pct=4.2))
    assert not workspace_summary_has_return_payload(_parsed_workspace_summary())


def test_should_fetch_independent_detail_views_requires_detail_preference_and_returns() -> None:
    parsed_summary = _parsed_workspace_summary(portfolio_return_pct=4.2)

    assert should_fetch_independent_detail_views(
        parsed_workspace_summary=parsed_summary,
        include_detail_blocks=True,
        prefer_independent_detail_analytics=True,
    )
    assert not should_fetch_independent_detail_views(
        parsed_workspace_summary=parsed_summary,
        include_detail_blocks=False,
        prefer_independent_detail_analytics=True,
    )
    assert not should_fetch_independent_detail_views(
        parsed_workspace_summary=parsed_summary,
        include_detail_blocks=True,
        prefer_independent_detail_analytics=False,
    )
    assert not should_fetch_independent_detail_views(
        parsed_workspace_summary=_parsed_workspace_summary(),
        include_detail_blocks=True,
        prefer_independent_detail_analytics=True,
    )


def test_build_summary_workspace_detail_views_preserves_summary_fallback() -> None:
    parsed_summary = _parsed_workspace_summary(portfolio_return_pct=4.2)

    detail_views = build_summary_workspace_detail_views(parsed_summary)

    assert detail_views.contribution == parsed_summary.contribution
    assert detail_views.attribution == parsed_summary.attribution
    assert detail_views.contribution_detail_result is None
    assert detail_views.attribution_detail_result is None
