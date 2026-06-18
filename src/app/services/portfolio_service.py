from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.contracts.portfolio import (
    PortfolioCatalogResponse,
    PortfolioExceptionSummary,
    PortfolioInsight,
    PortfolioInsightsResponse,
    PortfolioReadinessResponse,
)
from app.contracts.portfolio_activity_income import (
    PortfolioActivitySummaryResponse,
)
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioBookResponse,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioTopPosition,
)
from app.contracts.portfolio_liquidity import (
    PortfolioLiquidityResponse,
    PortfolioProjectedCashflowResponse,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.contracts.portfolio_workspace import PortfolioWorkspaceResponse
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.portfolio_book import build_portfolio_book_response
from app.services.portfolio_book_sources import (
    PortfolioBookSourceLoaders,
    PortfolioBookSourceRequest,
    PortfolioBookSourceResults,
    load_portfolio_book_source_results,
)
from app.services.portfolio_catalog_payloads import load_portfolio_catalog_response
from app.services.portfolio_exception_summaries import (
    PortfolioExceptionReadiness,
    build_portfolio_exception_summaries,
)
from app.services.portfolio_holdings_payloads import (
    PortfolioAllocationLoadRequest,
    PortfolioAllocationPayloadLoaders,
    PortfolioAllocationPayloads,
    PortfolioPositionBookLoadRequest,
    PortfolioPositionBookPayloadLoaders,
    PortfolioPositionBookPayloads,
    build_portfolio_allocation_response,
    load_portfolio_allocation_payloads,
    load_portfolio_position_book_payloads,
)
from app.services.portfolio_insights import build_portfolio_insights
from app.services.portfolio_liquidity_payloads import (
    PortfolioLiquidityLoadRequest,
    PortfolioLiquidityPayloadLoaders,
    PortfolioLiquidityPayloads,
    load_portfolio_liquidity_payloads,
)
from app.services.portfolio_liquidity_response import (
    build_portfolio_liquidity_response,
    build_projected_cashflow_response,
)
from app.services.portfolio_position_book import (
    build_position_book_response,
)
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
from app.services.portfolio_transaction_service import PortfolioTransactionServiceMixin
from app.services.portfolio_upstream_access import PortfolioUpstreamAccessMixin
from app.services.portfolio_upstream_payloads import (
    optional_payload,
    raise_on_upstream_client_error,
    require_payload,
)
from app.services.portfolio_workflow import (
    holdings_readiness_status,
    pricing_readiness_status,
    reporting_status_label,
    transactions_readiness_status,
)
from app.services.portfolio_workflow_service import PortfolioWorkflowServiceMixin
from app.services.portfolio_workspace_components import (
    assemble_portfolio_workspace_components,
    build_portfolio_workspace_assembly_state,
    build_portfolio_workspace_response_parts,
    extract_resolved_as_of_date,
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
from app.services.workspace_client_protocols import (
    PortfolioCoreClient,
    PortfolioManageClient,
    PortfolioPerformanceClient,
)

UpstreamResult = tuple[int, dict[str, Any]]


class PortfolioService(
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
        effective_as_of_date = as_of_date or datetime.now(UTC).date().isoformat()
        source_results = await self._load_portfolio_workspace_sources(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            effective_as_of_date=effective_as_of_date,
            reporting_currency=reporting_currency,
        )
        resolved_as_of_date = (
            extract_resolved_as_of_date(source_results.aum_result) or effective_as_of_date
        )
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
        effective_as_of_date: str,
        reporting_currency: str | None,
    ) -> PortfolioWorkspaceSourceResults:
        return await load_portfolio_workspace_sources(
            PortfolioWorkspaceSourceLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                effective_as_of_date=effective_as_of_date,
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
        return PortfolioInsightsResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=sources.workspace.as_of_date,
            insights=self._build_portfolio_insights(
                workspace=sources.workspace,
                positions=sources.positions.positions,
                top_positions=sources.positions.top_positions,
                allocation_views=sources.allocations.views,
                activity_summary=sources.activity,
            ),
            exception_summaries=self._build_portfolio_exception_summaries(
                workspace=sources.workspace,
                positions=sources.positions.positions,
                allocation_views=sources.allocations.views,
                transaction_total=sources.transactions.total,
            ),
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

    async def get_portfolio_book(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> PortfolioBookResponse:
        source_results = await self._load_portfolio_book_source_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            reporting_currency=reporting_currency,
        )
        return self._build_portfolio_book_response(
            correlation_id=correlation_id,
            source_results=source_results,
        )

    async def _load_portfolio_book_source_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None,
    ) -> PortfolioBookSourceResults:
        return await load_portfolio_book_source_results(
            PortfolioBookSourceRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
            PortfolioBookSourceLoaders(
                get_portfolio_allocations=self.get_portfolio_allocations,
                get_portfolio_positions=self.get_portfolio_positions,
                query_cash_balances_result=self._query_cash_balances_result,
                get_portfolio_result=self._get_portfolio_result,
            ),
        )

    def _build_portfolio_book_response(
        self,
        *,
        correlation_id: str,
        source_results: PortfolioBookSourceResults,
    ) -> PortfolioBookResponse:
        portfolio_payload = require_payload(
            result=source_results.portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        cash_balances_payload = require_payload(
            result=source_results.cash_balances_result,
            unavailable_detail_prefix="lotus-core cash balances unavailable",
        )
        return build_portfolio_book_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=source_results.positions.as_of_date,
            portfolio_payload=portfolio_payload,
            cash_balances_payload=cash_balances_payload,
            allocations=source_results.allocations,
            positions=source_results.positions,
        )

    async def get_portfolio_liquidity(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> PortfolioLiquidityResponse:
        payloads = await self._load_portfolio_liquidity_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        )
        return build_portfolio_liquidity_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            payloads=payloads,
        )

    async def _load_portfolio_liquidity_payloads(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None,
    ) -> PortfolioLiquidityPayloads:
        return await load_portfolio_liquidity_payloads(
            PortfolioLiquidityLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            PortfolioLiquidityPayloadLoaders(
                query_aum_result=self._query_aum_result,
                query_cash_balances_result=self._query_cash_balances_result,
                get_cashflow_projection_result=self._get_cashflow_projection_result,
                require_payload=require_payload,
            ),
        )

    async def get_portfolio_projected_cashflow(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        horizon_days: int,
        include_projected: bool,
    ) -> PortfolioProjectedCashflowResponse:
        cashflow_result = await self._get_cashflow_projection_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            horizon_days=horizon_days,
        )

        return build_projected_cashflow_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            cashflow_result=cashflow_result,
        )

    async def get_portfolio_allocations(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
        look_through_mode: str | None = "direct_only",
    ) -> PortfolioAllocationResponse:
        payloads = await self._load_portfolio_allocation_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            look_through_mode=look_through_mode,
        )
        return build_portfolio_allocation_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            reporting_currency=reporting_currency,
            aum_payload=payloads.aum_payload,
            positions_payload=payloads.positions_payload,
            allocation_payload=payloads.allocation_payload,
        )

    async def _load_portfolio_allocation_payloads(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None,
        look_through_mode: str | None,
    ) -> PortfolioAllocationPayloads:
        return await load_portfolio_allocation_payloads(
            PortfolioAllocationLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
                look_through_mode=look_through_mode,
            ),
            PortfolioAllocationPayloadLoaders(
                query_aum_result=self._query_aum_result,
                get_portfolio_positions_result=self._get_portfolio_positions_result,
                query_asset_allocation_result=self._query_asset_allocation_result,
                require_payload=require_payload,
            ),
        )

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> PortfolioPositionBookResponse:
        payloads = await self._load_position_book_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            reporting_currency=reporting_currency,
        )
        return build_position_book_response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            default_as_of_date=datetime.now(UTC).date().isoformat(),
            aum_payload=payloads.aum_payload,
            positions_payload=payloads.positions_payload,
        )

    async def _load_position_book_payloads(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None,
    ) -> PortfolioPositionBookPayloads:
        return await load_portfolio_position_book_payloads(
            PortfolioPositionBookLoadRequest(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
            PortfolioPositionBookPayloadLoaders(
                query_aum_result=self._query_aum_result,
                get_portfolio_positions_result=self._get_portfolio_positions_result,
                require_payload=require_payload,
            ),
        )

    def _build_portfolio_exception_summaries(
        self,
        *,
        workspace: PortfolioWorkspaceResponse,
        positions: list[PortfolioPositionView],
        allocation_views: list[PortfolioAllocationView],
        transaction_total: int,
    ) -> list[PortfolioExceptionSummary]:
        return build_portfolio_exception_summaries(
            readiness=PortfolioExceptionReadiness(
                holdings_status=holdings_readiness_status(
                    position_count=workspace.summary.position_count,
                    positions=positions,
                ),
                pricing_status=pricing_readiness_status(
                    positions=positions,
                    allocation_views=allocation_views,
                ),
                transaction_status=transactions_readiness_status(
                    transaction_total=transaction_total,
                    operations=workspace.operations,
                ),
                reporting_status=reporting_status_label(
                    workspace.reporting.status,
                    workspace.reporting.row_count,
                ),
            ),
            controls_blocking=(
                bool(workspace.operations.controls_blocking)
                if workspace.operations is not None
                else False
            ),
            partial_failures=workspace.partial_failures,
        )

    def _build_portfolio_insights(
        self,
        *,
        workspace: PortfolioWorkspaceResponse,
        positions: list[PortfolioPositionView],
        top_positions: list[PortfolioTopPosition],
        allocation_views: list[PortfolioAllocationView],
        activity_summary: PortfolioActivitySummaryResponse,
    ) -> list[PortfolioInsight]:
        return build_portfolio_insights(
            portfolio_id=workspace.portfolio.portfolio_id,
            summary=workspace.summary,
            positions=positions,
            top_positions=top_positions,
            activity_summary=activity_summary,
            pricing_status=pricing_readiness_status(
                positions=positions,
                allocation_views=allocation_views,
            ),
            reporting_status=reporting_status_label(
                workspace.reporting.status,
                workspace.reporting.row_count,
            ),
        )
