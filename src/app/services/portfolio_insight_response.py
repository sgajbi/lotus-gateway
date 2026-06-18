from dataclasses import dataclass

from app.contracts.portfolio import PortfolioInsightsResponse
from app.services.portfolio_exception_summaries import (
    PortfolioExceptionReadiness,
    build_portfolio_exception_summaries,
)
from app.services.portfolio_insights import build_portfolio_insights
from app.services.portfolio_readiness_insight_sources import PortfolioInsightSources
from app.services.portfolio_workflow import (
    holdings_readiness_status,
    pricing_readiness_status,
    reporting_status_label,
    transactions_readiness_status,
)


@dataclass(frozen=True)
class PortfolioInsightStatuses:
    holdings: str
    pricing: str
    transactions: str
    reporting: str


def build_portfolio_insights_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    sources: PortfolioInsightSources,
) -> PortfolioInsightsResponse:
    workspace = sources.workspace
    statuses = _portfolio_insight_statuses(sources)

    return PortfolioInsightsResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        as_of_date=workspace.as_of_date,
        insights=build_portfolio_insights(
            portfolio_id=workspace.portfolio.portfolio_id,
            summary=workspace.summary,
            positions=sources.positions.positions,
            top_positions=sources.positions.top_positions,
            activity_summary=sources.activity,
            pricing_status=statuses.pricing,
            reporting_status=statuses.reporting,
        ),
        exception_summaries=build_portfolio_exception_summaries(
            readiness=PortfolioExceptionReadiness(
                holdings_status=statuses.holdings,
                pricing_status=statuses.pricing,
                transaction_status=statuses.transactions,
                reporting_status=statuses.reporting,
            ),
            controls_blocking=_controls_blocking(sources),
            partial_failures=workspace.partial_failures,
        ),
    )


def _portfolio_insight_statuses(sources: PortfolioInsightSources) -> PortfolioInsightStatuses:
    workspace = sources.workspace
    positions = sources.positions.positions
    allocation_views = sources.allocations.views
    return PortfolioInsightStatuses(
        holdings=holdings_readiness_status(
            position_count=workspace.summary.position_count,
            positions=positions,
        ),
        pricing=pricing_readiness_status(
            positions=positions,
            allocation_views=allocation_views,
        ),
        transactions=transactions_readiness_status(
            transaction_total=sources.transactions.total,
            operations=workspace.operations,
        ),
        reporting=reporting_status_label(
            workspace.reporting.status,
            workspace.reporting.row_count,
        ),
    )


def _controls_blocking(sources: PortfolioInsightSources) -> bool:
    operations = sources.workspace.operations
    return bool(operations.controls_blocking) if operations is not None else False
