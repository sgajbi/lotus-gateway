import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.portfolio import (
    PortfolioCashflowOutlook,
    PortfolioCatalogResponse,
    PortfolioExceptionSummary,
    PortfolioInsight,
    PortfolioInsightsResponse,
    PortfolioLiquidityResponse,
    PortfolioOperationalReadiness,
    PortfolioPartialFailure,
    PortfolioPerformanceSummary,
    PortfolioProfile,
    PortfolioProjectedCashflowResponse,
    PortfolioReadinessResponse,
    PortfolioRebalanceSummary,
    PortfolioRebalanceSupportabilitySummary,
    PortfolioReportingReadiness,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceResponse,
)
from app.contracts.portfolio_activity_income import (
    PortfolioActivitySummaryResponse,
    PortfolioIncomeSummaryResponse,
)
from app.contracts.portfolio_core import PortfolioIdentity, PortfolioSummary
from app.contracts.portfolio_holdings import (
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioBookResponse,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioTopPosition,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.portfolio_catalog_payloads import parse_catalog_items
from app.services.portfolio_exception_summaries import (
    PortfolioExceptionReadiness,
    build_portfolio_exception_summaries,
)
from app.services.portfolio_holdings_payloads import (
    build_portfolio_allocation_response,
    parse_cash_balances,
)
from app.services.portfolio_insights import build_portfolio_insights
from app.services.portfolio_liquidity_payloads import (
    PortfolioLiquidityLoadRequest,
    PortfolioLiquidityPayloadLoaders,
    PortfolioLiquidityPayloads,
    load_portfolio_liquidity_payloads,
)
from app.services.portfolio_position_book import (
    build_top_positions,
    parse_position_book_summary,
    parse_positions,
)
from app.services.portfolio_source_readiness import (
    build_source_readiness_indicators,
    parse_portfolio_supportability,
    parse_readiness_bucket,
    parse_readiness_reasons,
)
from app.services.portfolio_transaction_ledger import (
    PortfolioTransactionsRequestContext,
    build_portfolio_transactions_request_context,
    build_transaction_ledger_response,
    build_transaction_rows_page_request_context,
    portfolio_transactions_cache_key,
    portfolio_transactions_client_kwargs,
)
from app.services.portfolio_transaction_summary import (
    InvalidPortfolioReportingWindow,
    PortfolioTransactionSummaryContext,
    PortfolioTransactionSummaryRequest,
    TransactionRowsPageRequest,
    build_activity_summary_response,
    build_income_summary_response,
    build_transaction_summary_context,
)
from app.services.portfolio_workflow import (
    build_readiness_indicators,
    build_workflow_actions,
    build_workflow_cues,
    holdings_readiness_status,
    pricing_readiness_status,
    reporting_status_label,
    transactions_readiness_status,
)
from app.services.portfolio_workspace_controls import build_workspace_control_capabilities
from app.services.portfolio_workspace_payloads import (
    optional_text,
    parse_cashflow_outlook,
    parse_operational_readiness,
    parse_portfolio_identity,
    parse_portfolio_profile,
    parse_portfolio_summary,
)
from app.services.portfolio_workspace_performance import parse_workspace_performance_summary
from app.services.portfolio_workspace_rebalance import (
    parse_workspace_rebalance_summary,
    parse_workspace_rebalance_supportability,
    rebalance_summary_from_supportability,
)
from app.services.portfolio_workspace_response import (
    PortfolioWorkspaceComponents,
    PortfolioWorkspaceResponseParts,
    assemble_portfolio_workspace_response,
)
from app.services.upstream_envelope import safe_upstream_detail
from app.services.workspace_client_protocols import (
    PortfolioCoreClient,
    PortfolioManageClient,
    PortfolioPerformanceClient,
)

UpstreamResult = tuple[int, dict[str, Any]]
PortfolioWorkspaceSourceResultSet = tuple[
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
    UpstreamResult,
]


@dataclass(frozen=True)
class PortfolioWorkspaceSourceResults:
    portfolio_result: UpstreamResult
    aum_result: UpstreamResult
    support_result: UpstreamResult
    cashflow_result: UpstreamResult
    cash_balance_result: UpstreamResult
    readiness_result: UpstreamResult


@dataclass(frozen=True)
class PortfolioWorkspaceAnalyticsResults:
    performance_result: UpstreamResult | None
    rebalance_result: UpstreamResult | None
    rebalance_supportability_result: UpstreamResult | None


@dataclass(frozen=True)
class PortfolioAllocationPayloads:
    aum_result: UpstreamResult
    aum_payload: dict[str, Any]
    positions_payload: dict[str, Any]
    allocation_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioPositionBookPayloads:
    aum_payload: dict[str, Any]
    positions_payload: dict[str, Any]


@dataclass(frozen=True)
class PortfolioAllocationResults:
    aum_result: UpstreamResult
    positions_result: UpstreamResult
    allocation_result: UpstreamResult


@dataclass(frozen=True)
class PortfolioInsightSources:
    workspace: PortfolioWorkspaceResponse
    positions: PortfolioPositionBookResponse
    allocations: PortfolioAllocationResponse
    transactions: PortfolioTransactionLedgerResponse
    activity: PortfolioActivitySummaryResponse


@dataclass(frozen=True)
class PortfolioReadinessSources:
    workspace: PortfolioWorkspaceResponse
    source_readiness: UpstreamResult
    positions: PortfolioPositionBookResponse
    allocations: PortfolioAllocationResponse
    transactions: PortfolioTransactionLedgerResponse


@dataclass(frozen=True)
class PortfolioWorkspaceAssemblyState:
    portfolio_payload: dict[str, Any]
    warnings: list[str]
    partial_failures: list[PortfolioPartialFailure]


@dataclass(frozen=True)
class PortfolioBookSourceResults:
    allocations: PortfolioAllocationResponse
    positions: PortfolioPositionBookResponse
    cash_balances_result: UpstreamResult
    portfolio_result: UpstreamResult


class PortfolioService:
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

    def clear_upstream_cache(self) -> None:
        self._upstream_cache.clear()

    async def _get_cached_upstream_result(
        self,
        key: tuple[object, ...],
        loader: Any,
    ) -> tuple[int, dict[str, Any]]:
        return await self._upstream_cache.get_or_set(key=key, factory=loader)

    async def _get_portfolio_result(
        self, portfolio_id: str, correlation_id: str
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("portfolio", portfolio_id),
            lambda: self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
        )

    async def _get_support_overview_result(
        self, portfolio_id: str, correlation_id: str
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("support_overview", portfolio_id),
            lambda: self._lotus_core_query_client.get_support_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
        )

    async def _query_aum_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("aum", portfolio_id, as_of_date, reporting_currency),
            lambda: self._lotus_core_query_client.query_assets_under_management(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
        )

    async def _query_cash_balances_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("cash_balances", portfolio_id, as_of_date, reporting_currency),
            lambda: self._lotus_core_query_client.get_portfolio_cash_balances(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
        )

    async def _get_cashflow_projection_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        horizon_days: int,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            (
                "cashflow_projection",
                portfolio_id,
                as_of_date,
                include_projected,
                horizon_days,
            ),
            lambda: self._lotus_core_query_client.get_cashflow_projection(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                horizon_days=horizon_days,
            ),
        )

    async def _query_asset_allocation_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        dimensions: list[str],
        reporting_currency: str | None = None,
        look_through_mode: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        dimensions_key = tuple(dimensions)
        return await self._get_cached_upstream_result(
            (
                "asset_allocation",
                portfolio_id,
                as_of_date,
                dimensions_key,
                reporting_currency,
                look_through_mode,
            ),
            lambda: self._lotus_core_query_client.query_asset_allocation(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                dimensions=dimensions,
                reporting_currency=reporting_currency,
                look_through_mode=look_through_mode,
            ),
        )

    async def _get_portfolio_positions_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("positions", portfolio_id, as_of_date, include_projected, reporting_currency),
            lambda: self._lotus_core_query_client.get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
        )

    async def _get_portfolio_transactions_result_for_context(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            portfolio_transactions_cache_key(context),
            lambda: self._fetch_portfolio_transactions(context),
        )

    async def _fetch_portfolio_transactions(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> tuple[int, dict[str, Any]]:
        return await self._lotus_core_query_client.get_portfolio_transactions(
            **portfolio_transactions_client_kwargs(context),
        )

    async def _get_portfolio_readiness_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("readiness", portfolio_id, as_of_date),
            lambda: self._lotus_core_query_client.get_portfolio_readiness(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
        )

    async def _get_portfolio_analytics_reference_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            ("portfolio_analytics_reference", portfolio_id, as_of_date),
            lambda: self._lotus_core_query_client.get_portfolio_analytics_reference(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            ),
        )

    async def _get_workspace_performance_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str,
    ) -> tuple[int, dict[str, Any]] | None:
        if self._analytics_client is None:
            return None
        reference_result = await self._get_portfolio_analytics_reference_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        report_end_date = as_of_date
        reference_payload = self._optional_payload(
            reference_result,
            "lotus-core",
            "IGNORED",
            [],
            [],
        )
        if isinstance(reference_payload, dict):
            reference_end_date = self._optional_str(reference_payload.get("performance_end_date"))
            if reference_end_date is not None:
                report_end_date = reference_end_date
        return await self._get_cached_upstream_result(
            ("workspace_performance", portfolio_id, report_end_date),
            lambda: self._analytics_client.get_twr_analytics(
                portfolio_id=portfolio_id,
                report_end_date=report_end_date,
                report_start_date=None,
                period="YTD",
                metric_basis="NET",
                benchmark_id=None,
                correlation_id=correlation_id,
            ),
        )

    async def _get_workspace_rebalance_result(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]] | None:
        if self._dpm_client is None:
            return None
        return await self._get_cached_upstream_result(
            ("workspace_rebalance", portfolio_id),
            lambda: self._dpm_client.list_runs(
                params={"portfolio_id": portfolio_id, "limit": 1},
                correlation_id=correlation_id,
            ),
        )

    async def _get_workspace_rebalance_supportability_result(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]] | None:
        if self._dpm_client is None:
            return None
        return await self._get_cached_upstream_result(
            ("workspace_rebalance_supportability",),
            lambda: self._dpm_client.get_supportability_summary(
                correlation_id=correlation_id,
            ),
        )

    async def get_portfolio_catalog(self, correlation_id: str) -> PortfolioCatalogResponse:
        status_code, payload = await self._lotus_core_query_client.list_portfolios(
            correlation_id=correlation_id
        )
        items_payload = self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core portfolio catalog unavailable",
        ).get("portfolios", [])
        items = parse_catalog_items(items_payload)
        return PortfolioCatalogResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            items=items,
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
            self._extract_resolved_as_of_date(source_results.aum_result) or effective_as_of_date
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
        (
            portfolio_result,
            aum_result,
            support_result,
            cashflow_result,
            cash_balance_result,
            readiness_result,
        ) = await self._gather_portfolio_workspace_source_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            effective_as_of_date=effective_as_of_date,
            reporting_currency=reporting_currency,
        )
        return PortfolioWorkspaceSourceResults(
            portfolio_result=portfolio_result,
            aum_result=aum_result,
            support_result=support_result,
            cashflow_result=cashflow_result,
            cash_balance_result=cash_balance_result,
            readiness_result=readiness_result,
        )

    async def _gather_portfolio_workspace_source_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        effective_as_of_date: str,
        reporting_currency: str | None,
    ) -> PortfolioWorkspaceSourceResultSet:
        return await asyncio.gather(
            self._get_portfolio_result(portfolio_id=portfolio_id, correlation_id=correlation_id),
            self._query_aum_result(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=effective_as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._get_support_overview_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._get_cashflow_projection_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=effective_as_of_date,
                include_projected=True,
                horizon_days=10,
            ),
            self._query_cash_balances_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=effective_as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._get_portfolio_readiness_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=effective_as_of_date,
            ),
        )

    async def _load_portfolio_workspace_analytics(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        performance_as_of_date: str,
    ) -> PortfolioWorkspaceAnalyticsResults:
        (
            performance_result,
            rebalance_result,
            rebalance_supportability_result,
        ) = await asyncio.gather(
            self._get_workspace_performance_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=performance_as_of_date,
            ),
            self._get_workspace_rebalance_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._get_workspace_rebalance_supportability_result(
                correlation_id=correlation_id,
            ),
        )
        return PortfolioWorkspaceAnalyticsResults(
            performance_result=performance_result,
            rebalance_result=rebalance_result,
            rebalance_supportability_result=rebalance_supportability_result,
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
        components = self._build_portfolio_workspace_components(
            source_results=source_results,
            analytics_results=analytics_results,
        )

        response_parts = self._build_portfolio_workspace_response_parts(
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

    def _build_portfolio_workspace_response_parts(
        self,
        *,
        portfolio_id: str,
        components: PortfolioWorkspaceComponents,
        source_results: PortfolioWorkspaceSourceResults,
        effective_as_of_date: str,
        resolved_as_of_date: str,
        reporting_currency: str | None,
    ) -> PortfolioWorkspaceResponseParts:
        return PortfolioWorkspaceResponseParts(
            reporting=self._reporting_readiness(
                components.summary,
                source_results.readiness_result,
            ),
            control_capabilities=self._build_workspace_control_capabilities(
                portfolio=components.portfolio,
                profile=components.profile,
                requested_as_of_date=effective_as_of_date,
                effective_as_of_date=resolved_as_of_date,
                requested_reporting_currency=reporting_currency,
            ),
            workflow_cues=build_workflow_cues(portfolio_id),
            warnings=components.warnings,
            partial_failures=components.partial_failures,
        )

    def _build_portfolio_workspace_components(
        self,
        *,
        source_results: PortfolioWorkspaceSourceResults,
        analytics_results: PortfolioWorkspaceAnalyticsResults,
    ) -> PortfolioWorkspaceComponents:
        assembly_state = self._portfolio_workspace_assembly_state(
            source_results=source_results,
        )
        return self._assemble_portfolio_workspace_components(
            source_results=source_results,
            analytics_results=analytics_results,
            assembly_state=assembly_state,
        )

    def _portfolio_workspace_assembly_state(
        self,
        *,
        source_results: PortfolioWorkspaceSourceResults,
    ) -> PortfolioWorkspaceAssemblyState:
        portfolio_payload = self._require_payload(
            result=source_results.portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        self._raise_on_upstream_client_error(
            source_results.support_result,
            detail_prefix="lotus-core support overview rejected the request",
        )
        self._raise_on_upstream_client_error(
            source_results.readiness_result,
            detail_prefix="lotus-core portfolio readiness rejected the request",
        )
        return PortfolioWorkspaceAssemblyState(
            portfolio_payload=portfolio_payload,
            warnings=[],
            partial_failures=[],
        )

    def _assemble_portfolio_workspace_components(
        self,
        *,
        source_results: PortfolioWorkspaceSourceResults,
        analytics_results: PortfolioWorkspaceAnalyticsResults,
        assembly_state: PortfolioWorkspaceAssemblyState,
    ) -> PortfolioWorkspaceComponents:
        summary = self._parse_summary(
            source_results.aum_result,
            source_results.cash_balance_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        )
        cashflow_outlook = self._parse_cashflow(
            source_results.cashflow_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        )
        performance = self._parse_workspace_performance(
            analytics_results.performance_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        )
        rebalance = self._parse_workspace_rebalance(
            analytics_results.rebalance_result,
            analytics_results.rebalance_supportability_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        )
        operations = self._parse_operations(
            source_results.support_result,
            assembly_state.warnings,
            assembly_state.partial_failures,
        )

        return PortfolioWorkspaceComponents(
            portfolio=self._parse_portfolio_identity(assembly_state.portfolio_payload),
            profile=self._parse_portfolio_profile(assembly_state.portfolio_payload),
            summary=summary,
            cashflow_outlook=cashflow_outlook,
            performance=performance,
            rebalance=rebalance,
            operations=operations,
            warnings=assembly_state.warnings,
            partial_failures=assembly_state.partial_failures,
        )

    async def get_portfolio_readiness(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioReadinessResponse:
        readiness_sources = await self._load_portfolio_readiness_sources(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        self._raise_on_upstream_client_error(
            readiness_sources.source_readiness,
            detail_prefix="lotus-core portfolio readiness rejected the request",
        )
        source_payload = self._optional_payload(
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
        workspace, source_readiness, positions, allocations, transactions = await asyncio.gather(
            self.get_portfolio_workspace(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._get_portfolio_readiness_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self.get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=False,
            ),
            self.get_portfolio_allocations(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._get_latest_transaction_probe(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
        )
        return PortfolioReadinessSources(
            workspace=workspace,
            source_readiness=source_readiness,
            positions=positions,
            allocations=allocations,
            transactions=transactions,
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
        indicators = build_source_readiness_indicators(
            payload=source_payload,
            detailed_view=False,
        ) or build_readiness_indicators(
            workspace=workspace,
            positions=positions.positions,
            allocation_views=allocations.views,
            transaction_total=transactions.total,
            detailed_view=False,
        )
        return PortfolioReadinessResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=workspace.as_of_date,
            holdings=parse_readiness_bucket((source_payload or {}).get("holdings")),
            pricing=parse_readiness_bucket((source_payload or {}).get("pricing")),
            transactions=parse_readiness_bucket((source_payload or {}).get("transactions")),
            reporting=parse_readiness_bucket((source_payload or {}).get("reporting")),
            blocking_reasons=parse_readiness_reasons(
                (source_payload or {}).get("blocking_reasons")
            ),
            supportability=parse_portfolio_supportability(
                (source_payload or {}).get("supportability")
            ),
            indicators=indicators,
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
        workspace, positions, allocations, transactions, activity = await asyncio.gather(
            self.get_portfolio_workspace(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self.get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=False,
            ),
            self.get_portfolio_allocations(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._get_latest_transaction_probe(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self.get_activity_summary(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                start_date=None,
                end_date=None,
            ),
        )
        return PortfolioInsightSources(
            workspace=workspace,
            positions=positions,
            allocations=allocations,
            transactions=transactions,
            activity=activity,
        )

    async def get_portfolio_workflow(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioWorkflowResponse:
        workspace, transactions = await asyncio.gather(
            self.get_portfolio_workspace(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._get_latest_transaction_probe(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
        )
        actions = build_workflow_actions(
            portfolio_id=portfolio_id,
            summary=workspace.summary,
            workflow_cues=workspace.workflow_cues,
            transaction_total=transactions.total,
        )
        return PortfolioWorkflowResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=workspace.as_of_date,
            actions=actions,
        )

    async def _get_latest_transaction_probe(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> PortfolioTransactionLedgerResponse:
        return await self.get_transaction_ledger(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=False,
            skip=0,
            limit=1,
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
        allocations, positions, cash_balances_result, portfolio_result = await asyncio.gather(
            self.get_portfolio_allocations(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            self.get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
            self._query_cash_balances_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._get_portfolio_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
        )
        return PortfolioBookSourceResults(
            allocations=allocations,
            positions=positions,
            cash_balances_result=cash_balances_result,
            portfolio_result=portfolio_result,
        )

    def _build_portfolio_book_response(
        self,
        *,
        correlation_id: str,
        source_results: PortfolioBookSourceResults,
    ) -> PortfolioBookResponse:
        portfolio_payload = self._require_payload(
            result=source_results.portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        cash_balances_payload = self._require_payload(
            result=source_results.cash_balances_result,
            unavailable_detail_prefix="lotus-core cash balances unavailable",
        )
        portfolio = self._parse_portfolio_identity(portfolio_payload)
        return PortfolioBookResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=source_results.positions.as_of_date,
            portfolio=portfolio,
            summary=source_results.positions.summary,
            cash_balances=parse_cash_balances(
                cash_balances_payload,
                source_results.positions.summary.assets_under_management_base,
            ),
            allocation_views=source_results.allocations.views,
            top_positions=source_results.positions.top_positions,
            positions=source_results.positions.positions,
        )

    async def get_portfolio_liquidity(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None = None,
    ) -> PortfolioLiquidityResponse:
        warnings: list[str] = []
        partial_failures: list[PortfolioPartialFailure] = []
        payloads = await self._load_portfolio_liquidity_payloads(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        )
        summary = self._parse_summary(
            payloads.aum_result,
            payloads.cash_balances_result,
            warnings,
            partial_failures,
        )
        return PortfolioLiquidityResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=str(
                payloads.aum_payload.get("resolved_as_of_date")
                or as_of_date
                or datetime.now(UTC).date()
            ),
            portfolio_id=portfolio_id,
            summary=summary,
            cash_balances=parse_cash_balances(
                payloads.cash_balances_payload,
                summary.assets_under_management_base,
            ),
            cashflow_outlook=self._parse_cashflow(
                payloads.cashflow_result,
                warnings,
                partial_failures,
            ),
            warnings=warnings,
            partial_failures=partial_failures,
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
                require_payload=self._require_payload,
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
        warnings: list[str] = []
        partial_failures: list[PortfolioPartialFailure] = []
        cashflow_result = await self._get_cashflow_projection_result(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            horizon_days=horizon_days,
        )
        cashflow_outlook = self._parse_cashflow(cashflow_result, warnings, partial_failures)
        resolved_as_of_date = self._extract_resolved_as_of_date(cashflow_result)

        return PortfolioProjectedCashflowResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=resolved_as_of_date or as_of_date or datetime.now(UTC).date().isoformat(),
            cashflow_outlook=cashflow_outlook,
            warnings=warnings,
            partial_failures=partial_failures,
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
        results = await self._query_portfolio_allocation_results(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            look_through_mode=look_through_mode,
        )
        return PortfolioAllocationPayloads(
            aum_result=results.aum_result,
            aum_payload=self._require_payload(
                result=results.aum_result,
                unavailable_detail_prefix="lotus-core aum unavailable",
            ),
            allocation_payload=self._require_payload(
                result=results.allocation_result,
                unavailable_detail_prefix="lotus-core allocation unavailable",
            ),
            positions_payload=self._require_payload(
                result=results.positions_result,
                unavailable_detail_prefix="lotus-core positions unavailable",
            ),
        )

    async def _query_portfolio_allocation_results(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None,
        look_through_mode: str | None,
    ) -> PortfolioAllocationResults:
        aum_result, positions_result, allocation_result = await asyncio.gather(
            self._query_aum_result(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._get_portfolio_positions_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=False,
                reporting_currency=reporting_currency,
            ),
            self._query_asset_allocation_result(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                dimensions=["asset_class", "currency", "sector", "region"],
                reporting_currency=reporting_currency,
                look_through_mode=look_through_mode,
            ),
        )
        return PortfolioAllocationResults(
            aum_result=aum_result,
            positions_result=positions_result,
            allocation_result=allocation_result,
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
        return self._build_position_book_response(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            payloads=payloads,
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
        aum_result, positions_result = await asyncio.gather(
            self._query_aum_result(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._get_portfolio_positions_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                reporting_currency=reporting_currency,
            ),
        )
        aum_payload = self._require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        )
        positions_payload = self._require_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        )
        return PortfolioPositionBookPayloads(
            aum_payload=aum_payload,
            positions_payload=positions_payload,
        )

    def _build_position_book_response(
        self,
        *,
        correlation_id: str,
        portfolio_id: str,
        as_of_date: str | None,
        payloads: PortfolioPositionBookPayloads,
    ) -> PortfolioPositionBookResponse:
        positions = parse_positions(payloads.positions_payload)
        summary = parse_position_book_summary(payloads.aum_payload, payloads.positions_payload)
        return PortfolioPositionBookResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=str(
                payloads.aum_payload.get("resolved_as_of_date")
                or as_of_date
                or datetime.now(UTC).date()
            ),
            summary=summary,
            top_positions=build_top_positions(positions),
            positions=positions,
        )

    async def get_transaction_ledger(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        skip: int,
        limit: int,
        transaction_type: str | None = None,
        security_id: str | None = None,
        instrument_id: str | None = None,
        component_type: str | None = None,
        linked_transaction_group_id: str | None = None,
        fx_contract_id: str | None = None,
        swap_event_id: str | None = None,
        near_leg_group_id: str | None = None,
        far_leg_group_id: str | None = None,
        sort_by: str = "transaction_date",
        sort_order: str = "desc",
        start_date: str | None = None,
        end_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioTransactionLedgerResponse:
        context = build_portfolio_transactions_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            skip=skip,
            limit=limit,
            transaction_type=transaction_type,
            security_id=security_id,
            instrument_id=instrument_id,
            component_type=component_type,
            linked_transaction_group_id=linked_transaction_group_id,
            fx_contract_id=fx_contract_id,
            swap_event_id=swap_event_id,
            near_leg_group_id=near_leg_group_id,
            far_leg_group_id=far_leg_group_id,
            sort_by=sort_by,
            sort_order=sort_order,
            start_date=start_date,
            end_date=end_date,
            reporting_currency=reporting_currency,
        )
        return self._build_transaction_ledger_response(
            context=context,
            result_payload=await self._load_transaction_ledger_payload(context),
        )

    async def _load_transaction_ledger_payload(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> dict[str, Any]:
        status_code, payload = await self._get_portfolio_transactions_result_for_context(context)
        return self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core transactions unavailable",
        )

    def _build_transaction_ledger_response(
        self,
        *,
        context: PortfolioTransactionsRequestContext,
        result_payload: dict[str, Any],
    ) -> PortfolioTransactionLedgerResponse:
        return build_transaction_ledger_response(
            context=context,
            contract_version=settings.contract_version,
            result_payload=result_payload,
        )

    async def get_income_summary(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioIncomeSummaryResponse:
        context = await self._load_transaction_summary_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            reporting_currency=reporting_currency,
        )
        return build_income_summary_response(
            context=context,
            contract_version=settings.contract_version,
        )

    async def get_activity_summary(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioActivitySummaryResponse:
        context = await self._load_transaction_summary_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            reporting_currency=reporting_currency,
        )
        return build_activity_summary_response(
            context=context,
            contract_version=settings.contract_version,
        )

    async def _load_transaction_summary_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        start_date: str | None,
        end_date: str | None,
        reporting_currency: str | None,
    ) -> PortfolioTransactionSummaryContext:
        try:
            return await build_transaction_summary_context(
                request=PortfolioTransactionSummaryRequest(
                    portfolio_id=portfolio_id,
                    correlation_id=correlation_id,
                    as_of_date=as_of_date,
                    start_date=start_date,
                    end_date=end_date,
                    reporting_currency=reporting_currency,
                ),
                page_loader=self._load_transaction_rows_page,
            )
        except InvalidPortfolioReportingWindow as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    def _require_payload(
        self, result: tuple[int, dict[str, Any]], unavailable_detail_prefix: str
    ) -> dict[str, Any]:
        status_code, payload = result
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=self._build_safe_upstream_error_detail(
                    unavailable_detail_prefix,
                    payload,
                ),
            )
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{unavailable_detail_prefix}: invalid payload",
            )
        return payload

    def _raise_on_upstream_client_error(
        self,
        result: tuple[int, dict[str, Any]],
        *,
        detail_prefix: str,
    ) -> None:
        status_code, payload = result
        if status.HTTP_400_BAD_REQUEST <= status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise HTTPException(
                status_code=status_code,
                detail=self._build_safe_upstream_error_detail(detail_prefix, payload),
            )

    def _build_safe_upstream_error_detail(
        self,
        detail_prefix: str,
        payload: dict[str, Any],
    ) -> str:
        detail = safe_upstream_detail(payload, default_detail="upstream request failed")
        return f"{detail_prefix}: {detail}"

    def _parse_portfolio_identity(self, payload: dict[str, Any]) -> PortfolioIdentity:
        return parse_portfolio_identity(payload)

    def _parse_portfolio_profile(self, payload: dict[str, Any]) -> PortfolioProfile:
        return parse_portfolio_profile(payload)

    def _parse_summary(
        self,
        aum_result: tuple[int, dict[str, Any]],
        cash_balances_result: tuple[int, dict[str, Any]],
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioSummary:
        aum_payload = (
            self._optional_payload(
                aum_result, "lotus-core", "PORTFOLIO_AUM_UNAVAILABLE", warnings, partial_failures
            )
            or {}
        )
        cash_payload = (
            self._optional_payload(
                cash_balances_result,
                "lotus-core",
                "PORTFOLIO_CASH_BALANCES_UNAVAILABLE",
                warnings,
                partial_failures,
            )
            or {}
        )
        return parse_portfolio_summary(
            aum_payload=aum_payload,
            cash_payload=cash_payload,
        )

    def _parse_cashflow(
        self,
        result: tuple[int, dict[str, Any]],
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioCashflowOutlook | None:
        payload = self._optional_payload(
            result, "lotus-core", "PORTFOLIO_CASHFLOW_UNAVAILABLE", warnings, partial_failures
        )
        if payload is None:
            return None
        return parse_cashflow_outlook(payload)

    def _parse_workspace_performance(
        self,
        result: tuple[int, dict[str, Any]] | None,
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioPerformanceSummary | None:
        if result is None:
            return None
        payload = self._optional_payload(
            result,
            "lotus-performance",
            "PORTFOLIO_PERFORMANCE_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        if payload is None:
            return None
        return parse_workspace_performance_summary(payload, warnings)

    def _parse_workspace_rebalance(
        self,
        result: tuple[int, dict[str, Any]] | None,
        supportability_result: tuple[int, dict[str, Any]] | None,
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioRebalanceSummary | None:
        supportability = self._parse_workspace_rebalance_supportability(
            supportability_result,
            warnings,
            partial_failures,
        )
        if result is None:
            return rebalance_summary_from_supportability("NO_RUNS", supportability)
        payload = self._optional_payload(
            result,
            "lotus-manage",
            "PORTFOLIO_REBALANCE_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        if payload is None:
            return rebalance_summary_from_supportability("UNKNOWN", supportability)
        return parse_workspace_rebalance_summary(payload, supportability)

    def _parse_workspace_rebalance_supportability(
        self,
        result: tuple[int, dict[str, Any]] | None,
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioRebalanceSupportabilitySummary | None:
        if result is None:
            return None
        payload = self._optional_payload(
            result,
            "lotus-manage",
            "PORTFOLIO_REBALANCE_SUPPORTABILITY_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        if payload is None:
            return None
        return parse_workspace_rebalance_supportability(payload, warnings, partial_failures)

    def _parse_operations(
        self,
        result: tuple[int, dict[str, Any]],
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioOperationalReadiness | None:
        payload = self._optional_payload(
            result,
            "lotus-core",
            "PORTFOLIO_SUPPORT_OVERVIEW_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        if payload is None:
            return None
        return parse_operational_readiness(payload)

    async def _load_transaction_rows_page(
        self,
        request: TransactionRowsPageRequest,
    ) -> dict[str, Any]:
        context = build_transaction_rows_page_request_context(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            skip=request.skip,
            limit=request.limit,
            start_date=request.start_date,
            end_date=request.end_date,
            reporting_currency=request.reporting_currency,
        )
        status_code, payload = await self._get_portfolio_transactions_result_for_context(context)
        return self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core transactions unavailable",
        )

    def _reporting_readiness(
        self,
        summary: PortfolioSummary,
        readiness_result: tuple[int, dict[str, Any]] | None = None,
    ):
        if readiness_result is not None:
            payload = self._optional_payload(
                readiness_result,
                "lotus-core",
                "PORTFOLIO_SOURCE_READINESS_UNAVAILABLE",
                [],
                [],
            )
            if payload is not None:
                reporting_bucket = payload.get("reporting")
                if isinstance(reporting_bucket, dict):
                    return PortfolioReportingReadiness(
                        status=str(reporting_bucket.get("status", "UNKNOWN")).strip().upper(),
                        row_count=summary.position_count,
                    )
        return PortfolioReportingReadiness(
            status="READY" if summary.position_count > 0 else "EMPTY",
            row_count=summary.position_count,
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

    def _optional_payload(
        self,
        result: tuple[int, dict[str, Any]],
        source_service: str,
        warning_code: str,
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> dict[str, Any] | None:
        status_code, payload = result
        if status_code < status.HTTP_400_BAD_REQUEST and isinstance(payload, dict):
            return payload
        warnings.append(warning_code)
        partial_failures.append(
            PortfolioPartialFailure(
                source_service=source_service,
                error_code=warning_code,
                detail=self._format_upstream_error_detail(payload),
            )
        )
        return None

    def _format_upstream_error_detail(self, payload: Any) -> str:
        if isinstance(payload, dict):
            detail = self._optional_str(payload.get("detail"))
            if detail is not None:
                return detail
        return str(payload)

    def _extract_resolved_as_of_date(self, result: tuple[int, dict[str, Any]]) -> str | None:
        payload = self._optional_payload(result, "lotus-core", "IGNORED", [], [])
        return (
            str(payload.get("resolved_as_of_date"))
            if payload and payload.get("resolved_as_of_date")
            else None
        )

    def _build_workspace_control_capabilities(
        self,
        *,
        portfolio: PortfolioIdentity,
        profile: PortfolioProfile,
        requested_as_of_date: str,
        effective_as_of_date: str,
        requested_reporting_currency: str | None,
    ) -> PortfolioWorkspaceControlCapabilities:
        return build_workspace_control_capabilities(
            portfolio=portfolio,
            profile=profile,
            requested_as_of_date=requested_as_of_date,
            effective_as_of_date=effective_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        )

    def _optional_str(self, value: Any) -> str | None:
        return optional_text(value)

    def _optional_int(self, value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
