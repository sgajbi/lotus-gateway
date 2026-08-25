from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.contracts.portfolio import (
    PortfolioCatalogResponse,
    PortfolioInsightsResponse,
    PortfolioReadinessResponse,
)
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioPositionBookResponse,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.contracts.portfolio_workspace import PortfolioWorkspaceResponse
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.portfolio_catalog_payloads import load_portfolio_catalog_response
from app.services.portfolio_client_protocols import (
    PortfolioCoreClient,
    PortfolioManageClient,
    PortfolioPerformanceClient,
)
from app.services.portfolio_holdings_service import PortfolioHoldingsServiceMixin
from app.services.portfolio_insight_response import build_portfolio_insights_response
from app.services.portfolio_readiness_insight_sources import (
    PortfolioInsightSourceLoaders,
    PortfolioInsightSourceRequest,
    PortfolioInsightSources,
    PortfolioReadinessSourceLoaders,
    PortfolioReadinessSourceRequest,
    PortfolioReadinessSources,
    load_portfolio_insight_sources,
    load_portfolio_readiness_sources,
)
from app.services.portfolio_readiness_response import (
    build_portfolio_readiness_response,
)
from app.services.portfolio_tax_lot_service import PortfolioTaxLotServiceMixin
from app.services.portfolio_transaction_service import PortfolioTransactionServiceMixin
from app.services.portfolio_upstream_access import PortfolioUpstreamAccessMixin
from app.services.portfolio_upstream_payloads import (
    optional_payload,
    raise_on_upstream_client_error,
)
from app.services.portfolio_workflow_service import PortfolioWorkflowServiceMixin
from app.services.portfolio_workspace_components import (
    assemble_portfolio_workspace_components,
    build_portfolio_workspace_assembly_state,
    build_portfolio_workspace_response_parts,
)
from app.services.portfolio_workspace_response import (
    assemble_portfolio_workspace_response,
)
from app.services.portfolio_workspace_sources import (
    PortfolioWorkspaceAnalyticsLoaders,
    PortfolioWorkspaceAnalyticsLoadRequest,
    PortfolioWorkspaceAnalyticsResults,
    PortfolioWorkspaceSourceLoaders,
    PortfolioWorkspaceSourceLoadRequest,
    PortfolioWorkspaceSourceResults,
    load_portfolio_workspace_analytics,
    load_portfolio_workspace_sources,
)

UpstreamResult = tuple[int, dict[str, Any]]


class PortfolioService(
    PortfolioHoldingsServiceMixin,
    PortfolioTaxLotServiceMixin,
    PortfolioWorkflowServiceMixin,
    PortfolioTransactionServiceMixin,
    PortfolioUpstreamAccessMixin,
):
    def __init__(
        self,
        lotus_core_query_client: PortfolioCoreClient,
        analytics_client: PortfolioPerformanceClient | None = None,
        dpm_client: PortfolioManageClient | None = None,
        upstream_cache_ttl_seconds: float | None = None,
    ):
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._dpm_client = dpm_client
        self._upstream_cache = AsyncTtlCache[tuple[int, dict[str, Any]]](
            ttl_seconds=upstream_cache_ttl_seconds or settings.portfolio_upstream_cache_ttl_seconds
        )

    async def get_portfolio_catalog(self, correlation_id: str) -> PortfolioCatalogResponse:
        return await load_portfolio_catalog_response(
            lotus_core_query_client=self._lotus_core_query_client,
            correlation_id=correlation_id,
        )

    async def get_portfolio_workspace(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioWorkspaceResponse:
        source_results = await self._load_portfolio_workspace_sources(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            requested_as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        )
        resolved_as_of_date = (
            source_results.resolved_as_of_date or as_of_date or datetime.now(UTC).date().isoformat()
        )
        effective_as_of_date = as_of_date or resolved_as_of_date
        performance_as_of_date = as_of_date or resolved_as_of_date
        analytics_results = await self._load_portfolio_workspace_analytics(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            performance_as_of_date=performance_as_of_date,
        )
        return self._build_portfolio_workspace_response(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            effective_as_of_date=effective_as_of_date,
            resolved_as_of_date=resolved_as_of_date,
            reporting_currency=reporting_currency,
            source_results=source_results,
            analytics_results=analytics_results,
        )

    async def _load_portfolio_workspace_sources(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        requested_as_of_date: str | None,
        reporting_currency: str | None,
    ) -> PortfolioWorkspaceSourceResults:
        return await load_portfolio_workspace_sources(
            PortfolioWorkspaceSourceLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                requested_as_of_date=requested_as_of_date,
                reporting_currency=reporting_currency,
            ),
            PortfolioWorkspaceSourceLoaders(
                get_portfolio_result=self._get_portfolio_result,
                query_aum_result=self._query_aum_result,
                get_support_overview_result=self._get_support_overview_result,
                get_cashflow_projection_result=self._get_cashflow_projection_result,
                query_cash_balances_result=self._query_cash_balances_result,
                get_portfolio_readiness_result=self._get_portfolio_readiness_result,
            ),
        )

    async def _load_portfolio_workspace_analytics(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        performance_as_of_date: str,
    ) -> PortfolioWorkspaceAnalyticsResults:
        return await load_portfolio_workspace_analytics(
            PortfolioWorkspaceAnalyticsLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                performance_as_of_date=performance_as_of_date,
            ),
            PortfolioWorkspaceAnalyticsLoaders(
                get_workspace_performance_result=self._get_workspace_performance_result,
                get_workspace_rebalance_result=self._get_workspace_rebalance_result,
                get_workspace_rebalance_supportability_result=(
                    self._get_workspace_rebalance_supportability_result
                ),
            ),
        )

    def _build_portfolio_workspace_response(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        effective_as_of_date: str,
        resolved_as_of_date: str,
        reporting_currency: str | None,
        source_results: PortfolioWorkspaceSourceResults,
        analytics_results: PortfolioWorkspaceAnalyticsResults,
    ) -> PortfolioWorkspaceResponse:
        assembly_state = build_portfolio_workspace_assembly_state(
            source_results=source_results,
        )
        components = assemble_portfolio_workspace_components(
            source_results=source_results,
            analytics_results=analytics_results,
            assembly_state=assembly_state,
        )
        response_parts = build_portfolio_workspace_response_parts(
            portfolio_id=portfolio_id,
            components=components,
            source_results=source_results,
            effective_as_of_date=effective_as_of_date,
            resolved_as_of_date=resolved_as_of_date,
            reporting_currency=reporting_currency,
        )

        return assemble_portfolio_workspace_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=resolved_as_of_date,
            components=components,
            response_parts=response_parts,
        )

    async def get_portfolio_readiness(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioReadinessResponse:
        readiness_sources = await self._load_portfolio_readiness_sources(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        raise_on_upstream_client_error(
            readiness_sources.source_readiness,
            detail_prefix="lotus-core portfolio readiness rejected the request",
        )
        source_payload = optional_payload(
            readiness_sources.source_readiness,
            "lotus-core",
            "PORTFOLIO_SOURCE_READINESS_UNAVAILABLE",
            [],
            [],
        )
        return self._build_portfolio_readiness_response(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            workspace=readiness_sources.workspace,
            positions=readiness_sources.positions,
            allocations=readiness_sources.allocations,
            transactions=readiness_sources.transactions,
            source_payload=source_payload,
        )

    async def _load_portfolio_readiness_sources(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> PortfolioReadinessSources:
        return await load_portfolio_readiness_sources(
            PortfolioReadinessSourceRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            PortfolioReadinessSourceLoaders(
                get_portfolio_workspace=self.get_portfolio_workspace,
                get_portfolio_readiness_result=self._get_portfolio_readiness_result,
                get_portfolio_positions=self.get_portfolio_positions,
                get_portfolio_allocations=self.get_portfolio_allocations,
                get_latest_transaction_probe=self._get_latest_transaction_probe,
            ),
        )

    def _build_portfolio_readiness_response(
        self,
        *,
        correlation_id: str,
        portfolio_id: str,
        workspace: PortfolioWorkspaceResponse,
        positions: PortfolioPositionBookResponse,
        allocations: PortfolioAllocationResponse,
        transactions: PortfolioTransactionLedgerResponse,
        source_payload: dict[str, Any] | None,
    ) -> PortfolioReadinessResponse:
        return build_portfolio_readiness_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            workspace=workspace,
            positions=positions,
            allocations=allocations,
            transactions=transactions,
            source_payload=source_payload,
        )

    async def get_portfolio_insights(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioInsightsResponse:
        sources = await self._load_portfolio_insight_sources(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        return build_portfolio_insights_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            sources=sources,
        )

    async def _load_portfolio_insight_sources(
        self, *, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioInsightSources:
        return await load_portfolio_insight_sources(
            PortfolioInsightSourceRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            PortfolioInsightSourceLoaders(
                get_portfolio_workspace=self.get_portfolio_workspace,
                get_portfolio_positions=self.get_portfolio_positions,
                get_portfolio_allocations=self.get_portfolio_allocations,
                get_latest_transaction_probe=self._get_latest_transaction_probe,
                get_activity_summary=self.get_activity_summary,
            ),
        )
