import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.portfolio import (
    PortfolioActivitySummaryResponse,
    PortfolioAllocationBucket,
    PortfolioAllocationLookThroughCapability,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioBookResponse,
    PortfolioCashBalance,
    PortfolioCashflowOutlook,
    PortfolioCashflowPoint,
    PortfolioCatalogItem,
    PortfolioCatalogResponse,
    PortfolioExceptionSummary,
    PortfolioIdentity,
    PortfolioIncomeSummaryResponse,
    PortfolioInsight,
    PortfolioInsightsResponse,
    PortfolioLiquidityResponse,
    PortfolioOperationalReadiness,
    PortfolioPartialFailure,
    PortfolioPerformanceSummary,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioProfile,
    PortfolioProjectedCashflowResponse,
    PortfolioReadinessIndicator,
    PortfolioReadinessResponse,
    PortfolioRebalanceSummary,
    PortfolioRebalanceSupportabilitySummary,
    PortfolioReportingReadiness,
    PortfolioSummary,
    PortfolioTopPosition,
    PortfolioTransactionLedgerResponse,
    PortfolioWorkflowAction,
    PortfolioWorkflowLaunchCue,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceResponse,
)
from app.precision_policy import (
    quantize_money,
    quantize_performance,
)
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.portfolio_exception_summaries import (
    PortfolioExceptionReadiness,
    build_portfolio_exception_summaries,
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
    PortfolioTransactionSummaryContext,
    build_activity_summary_response,
    build_income_summary_response,
    transaction_date_in_range,
    transaction_date_value,
)
from app.services.portfolio_workspace_controls import build_workspace_control_capabilities
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


@dataclass(frozen=True)
class PortfolioWorkflowActionSpec:
    title: str
    impact: str
    target: str
    href: str
    cta_label: str
    recommended: bool = False


EMPTY_PORTFOLIO_WORKFLOW_ACTION_SPECS: tuple[PortfolioWorkflowActionSpec, ...] = (
    PortfolioWorkflowActionSpec(
        title="Fund portfolio",
        impact=(
            "Create opening liquidity so balances, allocation, and readiness checks become "
            "meaningful."
        ),
        target="Target: cash funding and opening balance setup",
        href="operations",
        cta_label="Fund now",
        recommended=True,
    ),
    PortfolioWorkflowActionSpec(
        title="Book first trade",
        impact="Activate the holdings book and create the first investable position.",
        target="Target: transaction entry and execution workflow",
        href="operations",
        cta_label="Book trade",
    ),
    PortfolioWorkflowActionSpec(
        title="Publish pricing",
        impact="Enable valuation, allocation, and downstream reporting coverage.",
        target="Target: pricing publication and valuation refresh",
        href="operations",
        cta_label="Publish prices",
    ),
    PortfolioWorkflowActionSpec(
        title="Review holdings",
        impact="Confirm the funded book, position weights, and coverage after valuation.",
        target="Target: holdings and allocation review",
        href="#portfolio-insights",
        cta_label="Open holdings",
    ),
    PortfolioWorkflowActionSpec(
        title="Open performance",
        impact="Review return analytics once holdings are funded and valued.",
        target="Target: performance workspace after valuation is available",
        href="performance",
        cta_label="Open performance",
    ),
)


class PortfolioService:
    _WORKFLOW_DEFINITIONS: dict[str, dict[str, str | int]] = {
        "performance": {
            "order": 0,
            "title": "Review performance",
            "cta_label": "Performance",
            "target_label": "Performance",
            "impact": (
                "Review portfolio return, benchmark context, and contribution once the book "
                "is valued."
            ),
        },
        "holdings": {
            "order": 1,
            "title": "Review holdings",
            "cta_label": "Holdings",
            "target_label": "Holdings",
            "impact": (
                "Confirm funded positions, valuations, and portfolio weights before client review."
            ),
        },
        "transactions": {
            "order": 2,
            "title": "Review transactions",
            "cta_label": "Transactions",
            "target_label": "Transactions",
            "impact": "Inspect recent funding, trading, and cash activity affecting the book.",
        },
        "risk": {
            "order": 3,
            "title": "Review suitability",
            "cta_label": "Suitability",
            "target_label": "Suitability",
            "impact": (
                "Validate suitability, exposure, and mandate fit before the next client action."
            ),
        },
        "proposal": {
            "order": 4,
            "title": "Prepare recommendation",
            "cta_label": "Recommendation",
            "target_label": "Recommendation",
            "impact": "Prepare the next recommended portfolio action or client proposal.",
        },
    }

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
        items = [self._parse_catalog_item(item) for item in items_payload if isinstance(item, dict)]
        items.sort(key=lambda item: item.portfolio_id)
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
            workflow_cues=self._build_workflow_cues(portfolio_id),
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
        ) or self._build_readiness_indicators(
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
        actions = self._build_workflow_actions(
            portfolio_id=portfolio_id,
            summary=workspace.summary,
            operations=workspace.operations,
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
            cash_balances=self._parse_cash_balances(
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
            cash_balances=self._parse_cash_balances(
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
        summary = parse_position_book_summary(
            payloads.aum_payload,
            payloads.positions_payload,
        )
        return PortfolioAllocationResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=str(
                payloads.aum_payload.get("resolved_as_of_date")
                or as_of_date
                or datetime.now(UTC).date()
            ),
            reporting_currency=self._optional_str(
                payloads.allocation_payload.get("reporting_currency")
            )
            or reporting_currency,
            look_through=self._parse_look_through_capability(
                payloads.allocation_payload.get("look_through")
            ),
            summary=summary,
            views=self._parse_allocation_views(payloads.allocation_payload),
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
        window_start, window_end = self._resolve_reporting_window(
            start_date,
            end_date,
            default_end_date=as_of_date,
        )
        ytd_start = date(window_end.year, 1, 1)
        resolved_reporting_currency, year_to_date_rows = await self._list_transaction_rows(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            start_date=ytd_start.isoformat(),
            end_date=window_end.isoformat(),
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
        )
        requested_window_rows = [
            item
            for item in year_to_date_rows
            if transaction_date_in_range(
                transaction_date=transaction_date_value(item),
                start_date=window_start,
                end_date=window_end,
            )
        ]
        return PortfolioTransactionSummaryContext(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            reporting_currency=resolved_reporting_currency or reporting_currency or "USD",
            window_start=window_start,
            window_end=window_end,
            requested_window_rows=requested_window_rows,
            year_to_date_rows=year_to_date_rows,
        )

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

    def _parse_catalog_item(self, item: dict[str, Any]) -> PortfolioCatalogItem:
        portfolio_id = str(item.get("portfolio_id", "")).strip()
        return PortfolioCatalogItem(
            portfolio_id=portfolio_id,
            display_name=self._resolve_portfolio_display_name(
                item, fallback_portfolio_id=portfolio_id
            ),
            base_currency=str(item.get("base_currency", "USD")),
            client_id=self._optional_str(item.get("client_id", item.get("cif_id"))),
            booking_center_code=self._optional_str(
                item.get("booking_center_code", item.get("booking_center"))
            ),
            portfolio_type=self._optional_str(item.get("portfolio_type")),
            status=self._optional_str(item.get("status")),
        )

    def _parse_portfolio_identity(self, payload: dict[str, Any]) -> PortfolioIdentity:
        portfolio_id = str(payload.get("portfolio_id", ""))
        return PortfolioIdentity(
            portfolio_id=portfolio_id,
            display_name=self._resolve_portfolio_display_name(
                payload, fallback_portfolio_id=portfolio_id
            ),
            client_id=self._optional_str(payload.get("client_id", payload.get("cif_id"))),
            base_currency=str(payload.get("base_currency", "USD")),
            booking_center_code=self._optional_str(
                payload.get("booking_center_code", payload.get("booking_center"))
            ),
        )

    def _parse_portfolio_profile(self, payload: dict[str, Any]) -> PortfolioProfile:
        return PortfolioProfile(
            status=self._optional_str(payload.get("status")),
            portfolio_type=self._optional_str(payload.get("portfolio_type")),
            risk_exposure=self._optional_str(payload.get("risk_exposure")),
            investment_time_horizon=self._optional_str(payload.get("investment_time_horizon")),
            objective=self._optional_str(payload.get("objective")),
            is_leverage_allowed=payload.get("is_leverage_allowed"),
            advisor_id=self._optional_str(payload.get("advisor_id")),
            open_date=self._optional_str(payload.get("open_date")),
            close_date=self._optional_str(payload.get("close_date")),
        )

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
        first_portfolio: dict[str, Any] = next(iter(aum_payload.get("portfolios", [])), {})
        invested = float(quantize_money(first_portfolio.get("aum_reporting_currency", 0)))
        cash_total = float(
            quantize_money(
                cash_payload.get("totals", {}).get("total_balance_reporting_currency", 0)
            )
        )
        total_aum = invested
        cash_weight = (
            float(quantize_performance((cash_total / total_aum) * 100)) if total_aum > 0 else 0.0
        )
        return PortfolioSummary(
            assets_under_management_base=total_aum,
            invested_market_value_base=float(quantize_money(total_aum - cash_total)),
            cash_market_value_base=cash_total,
            cash_weight_pct=cash_weight,
            position_count=int(first_portfolio.get("position_count", 0)),
            cash_balance_count=int(cash_payload.get("totals", {}).get("cash_account_count", 0)),
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
        return PortfolioCashflowOutlook(
            as_of_date=str(payload.get("as_of_date")),
            range_end_date=str(payload.get("range_end_date")),
            total_net_cashflow_base=float(quantize_money(payload.get("total_net_cashflow", 0))),
            projection_days=int(payload.get("projection_days", 0)),
            include_projected=bool(payload.get("include_projected", False)),
            upcoming_points=[
                PortfolioCashflowPoint(
                    projection_date=str(point.get("projection_date")),
                    net_cashflow_base=float(quantize_money(point.get("net_cashflow", 0))),
                    projected_cumulative_cashflow_base=float(
                        quantize_money(point.get("projected_cumulative_cashflow", 0))
                    ),
                )
                for point in payload.get("points", [])
                if isinstance(point, dict)
            ],
        )

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
        return PortfolioOperationalReadiness(
            **{key: payload.get(key) for key in PortfolioOperationalReadiness.model_fields}
        )

    def _parse_allocation_views(self, payload: dict[str, Any]) -> list[PortfolioAllocationView]:
        return [
            PortfolioAllocationView(
                dimension=str(view.get("dimension")),
                buckets=[
                    PortfolioAllocationBucket(
                        bucket=str(bucket.get("dimension_value")),
                        position_count=int(bucket.get("position_count", 0)),
                        market_value_base=float(
                            quantize_money(bucket.get("market_value_reporting_currency", 0))
                        ),
                        weight_pct=float(
                            quantize_performance(float(bucket.get("weight", 0)) * 100)
                        ),
                    )
                    for bucket in view.get("buckets", [])
                    if isinstance(bucket, dict)
                ],
            )
            for view in payload.get("views", [])
            if isinstance(view, dict)
        ]

    def _parse_cash_balances(
        self, payload: dict[str, Any], total_aum: float
    ) -> list[PortfolioCashBalance]:
        balances: list[PortfolioCashBalance] = []
        for item in payload.get("cash_accounts", []):
            balance = float(quantize_money(item.get("balance_reporting_currency", 0)))
            weight = (
                float(quantize_performance((balance / total_aum) * 100)) if total_aum > 0 else 0.0
            )
            balances.append(
                PortfolioCashBalance(
                    security_id=str(item.get("security_id", "")),
                    instrument_name=str(item.get("instrument_name", "")),
                    currency=self._optional_str(item.get("account_currency")),
                    quantity=float(quantize_money(item.get("balance_account_currency", 0))),
                    market_value_base=balance,
                    weight_pct=weight,
                )
            )
        return balances

    async def _list_transaction_rows(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        start_date: str,
        end_date: str,
        as_of_date: str | None,
        reporting_currency: str | None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        page_size = 500
        rows: list[dict[str, Any]] = []
        resolved_reporting_currency: str | None = None
        skip = 0

        while True:
            result_payload = await self._load_transaction_rows_page(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                skip=skip,
                limit=page_size,
                start_date=start_date,
                end_date=end_date,
                reporting_currency=reporting_currency,
            )
            if resolved_reporting_currency is None:
                resolved_reporting_currency = self._optional_str(
                    result_payload.get("reporting_currency")
                )
            page_rows = self._transaction_page_rows(result_payload)
            rows.extend(page_rows)
            total = int(result_payload.get("total", len(page_rows)))
            skip += len(page_rows)
            if not page_rows or skip >= total:
                break

        return resolved_reporting_currency, rows

    async def _load_transaction_rows_page(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        skip: int,
        limit: int,
        start_date: str,
        end_date: str,
        reporting_currency: str | None,
    ) -> dict[str, Any]:
        context = build_transaction_rows_page_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            reporting_currency=reporting_currency,
        )
        status_code, payload = await self._get_portfolio_transactions_result_for_context(context)
        return self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core transactions unavailable",
        )

    @staticmethod
    def _transaction_page_rows(result_payload: dict[str, Any]) -> list[dict[str, Any]]:
        return [item for item in result_payload.get("transactions", []) if isinstance(item, dict)]

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

    def _build_workflow_cues(self, portfolio_id: str) -> list[PortfolioWorkflowLaunchCue]:
        return [
            PortfolioWorkflowLaunchCue(
                key="holdings",
                label="Holdings",
                href=f"/portfolio?portfolioId={portfolio_id}#portfolio-drilldown",
            ),
            PortfolioWorkflowLaunchCue(
                key="transactions",
                label="Transactions",
                href=f"/portfolio?portfolioId={portfolio_id}#portfolio-drilldown",
            ),
            PortfolioWorkflowLaunchCue(
                key="performance",
                label="Performance",
                href=f"/performance?portfolioId={portfolio_id}",
            ),
        ]

    def _build_readiness_indicators(
        self,
        *,
        workspace: PortfolioWorkspaceResponse,
        positions: list[PortfolioPositionView],
        allocation_views: list[PortfolioAllocationView],
        transaction_total: int,
        detailed_view: bool,
    ) -> list[PortfolioReadinessIndicator]:
        holdings_status = self._holdings_readiness_status(
            position_count=workspace.summary.position_count,
            positions=positions,
        )
        pricing_status = self._pricing_readiness_status(
            positions=positions,
            allocation_views=allocation_views,
        )
        transactions_status = self._transactions_readiness_status(
            transaction_total=transaction_total,
            operations=workspace.operations,
        )
        reporting_status = self._reporting_status_label(
            workspace.reporting.status,
            workspace.reporting.row_count,
        )
        return self._readiness_indicators_from_statuses(
            holdings_status=holdings_status,
            pricing_status=pricing_status,
            transactions_status=transactions_status,
            reporting_status=reporting_status,
            detailed_view=detailed_view,
        )

    def _readiness_indicators_from_statuses(
        self,
        *,
        holdings_status: str,
        pricing_status: str,
        transactions_status: str,
        reporting_status: str,
        detailed_view: bool,
    ) -> list[PortfolioReadinessIndicator]:
        insights_href = "#portfolio-drilldown" if detailed_view else "#portfolio-insights"

        return [
            self._readiness_indicator(
                key="holdings",
                label="Holdings",
                status=holdings_status,
                href=insights_href,
            ),
            self._readiness_indicator(
                key="pricing",
                label="Pricing",
                status=pricing_status,
                href="#portfolio-attention",
            ),
            self._readiness_indicator(
                key="transactions",
                label="Transactions",
                status=transactions_status,
                href=insights_href,
            ),
            self._readiness_indicator(
                key="reporting",
                label="Reporting",
                status=reporting_status,
                href="#portfolio-health",
            ),
        ]

    def _readiness_indicator(
        self, *, key: str, label: str, status: str, href: str
    ) -> PortfolioReadinessIndicator:
        return PortfolioReadinessIndicator(
            key=key,
            label=label,
            status=status,
            href=href,
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
                holdings_status=self._holdings_readiness_status(
                    position_count=workspace.summary.position_count,
                    positions=positions,
                ),
                pricing_status=self._pricing_readiness_status(
                    positions=positions,
                    allocation_views=allocation_views,
                ),
                transaction_status=self._transactions_readiness_status(
                    transaction_total=transaction_total,
                    operations=workspace.operations,
                ),
                reporting_status=self._reporting_status_label(
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
            pricing_status=self._pricing_readiness_status(
                positions=positions,
                allocation_views=allocation_views,
            ),
            reporting_status=self._reporting_status_label(
                workspace.reporting.status,
                workspace.reporting.row_count,
            ),
        )

    def _build_workflow_actions(
        self,
        *,
        portfolio_id: str,
        summary: PortfolioSummary,
        operations: PortfolioOperationalReadiness | None,
        workflow_cues: list[PortfolioWorkflowLaunchCue],
        transaction_total: int,
    ) -> list[PortfolioWorkflowAction]:
        if self._is_empty_portfolio_workflow(summary, transaction_total):
            return self._build_empty_portfolio_workflow_actions(portfolio_id)
        return self._build_supported_cue_workflow_actions(workflow_cues)

    def _build_empty_portfolio_workflow_actions(
        self,
        portfolio_id: str,
    ) -> list[PortfolioWorkflowAction]:
        return [
            PortfolioWorkflowAction(
                sequence=index + 1,
                title=spec.title,
                impact=spec.impact,
                target=spec.target,
                href=self._workflow_action_spec_href(spec, portfolio_id),
                cta_label=spec.cta_label,
                recommended=spec.recommended,
            )
            for index, spec in enumerate(EMPTY_PORTFOLIO_WORKFLOW_ACTION_SPECS)
        ]

    def _build_supported_cue_workflow_actions(
        self,
        workflow_cues: list[PortfolioWorkflowLaunchCue],
    ) -> list[PortfolioWorkflowAction]:
        ordered_cues = sorted(
            self._supported_workflow_cues(self._dedupe_workflow_cues(workflow_cues)),
            key=lambda cue: self._workflow_order_rank(cue.key),
        )
        return [
            self._build_supported_cue_workflow_action(
                cue=cue,
                sequence=index + 1,
                recommended=index == 0,
            )
            for index, cue in enumerate(ordered_cues)
        ]

    def _build_supported_cue_workflow_action(
        self,
        *,
        cue: PortfolioWorkflowLaunchCue,
        sequence: int,
        recommended: bool,
    ) -> PortfolioWorkflowAction:
        return PortfolioWorkflowAction(
            sequence=sequence,
            title=self._workflow_task_label(cue.key),
            impact=self._workflow_impact_label(cue.key),
            target=f"Target: {self._workflow_target_label(cue.key)} workflow for this portfolio",
            href=cue.href,
            cta_label=self._workflow_cta_label(cue.key),
            recommended=recommended,
        )

    def _is_empty_portfolio_workflow(
        self,
        summary: PortfolioSummary,
        transaction_total: int,
    ) -> bool:
        return (
            summary.position_count == 0
            and summary.cash_balance_count == 0
            and transaction_total == 0
        )

    def _workflow_action_spec_href(
        self,
        spec: PortfolioWorkflowActionSpec,
        portfolio_id: str,
    ) -> str:
        if spec.href == "operations":
            return f"/workbench?portfolioId={portfolio_id}"
        if spec.href == "performance":
            return f"/performance?portfolioId={portfolio_id}"
        return spec.href

    def _holdings_readiness_status(
        self, *, position_count: int, positions: list[PortfolioPositionView]
    ) -> str:
        if position_count > 0 and positions:
            return "Ready"
        if position_count > 0:
            return "Partial"
        return "Missing"

    def _pricing_readiness_status(
        self,
        *,
        positions: list[PortfolioPositionView],
        allocation_views: list[PortfolioAllocationView],
    ) -> str:
        has_valued_holdings = any((position.market_value_base or 0) > 0 for position in positions)
        if has_valued_holdings and allocation_views:
            return "Ready"
        if positions or allocation_views:
            return "Partial"
        return "Missing"

    def _transactions_readiness_status(
        self,
        *,
        transaction_total: int,
        operations: PortfolioOperationalReadiness | None,
    ) -> str:
        if transaction_total > 0:
            return "Ready"
        if operations and operations.latest_booked_transaction_date:
            return "Partial"
        return "Missing"

    def _reporting_status_label(self, status: str, row_count: int) -> str:
        normalized = status.upper()
        if normalized in {"READY", "COMPLETE"}:
            return "Ready"
        if normalized == "EMPTY":
            return "Empty"
        if normalized == "PENDING" or row_count > 0:
            return "Partial"
        return "Missing"

    def _dedupe_workflow_cues(
        self, workflow_cues: list[PortfolioWorkflowLaunchCue]
    ) -> list[PortfolioWorkflowLaunchCue]:
        unique: list[PortfolioWorkflowLaunchCue] = []
        seen: set[str] = set()
        for cue in workflow_cues:
            if cue.key in seen:
                continue
            seen.add(cue.key)
            unique.append(cue)
        return unique

    def _supported_workflow_cues(
        self, workflow_cues: list[PortfolioWorkflowLaunchCue]
    ) -> list[PortfolioWorkflowLaunchCue]:
        return [cue for cue in workflow_cues if cue.key in self._WORKFLOW_DEFINITIONS]

    def _workflow_order_rank(self, key: str) -> int:
        definition = self._WORKFLOW_DEFINITIONS.get(key)
        return int(definition["order"]) if definition is not None else 99

    def _workflow_task_label(self, key: str) -> str:
        definition = self._WORKFLOW_DEFINITIONS.get(key)
        return str(definition["title"]) if definition is not None else "Open workflow"

    def _workflow_cta_label(self, key: str) -> str:
        definition = self._WORKFLOW_DEFINITIONS.get(key)
        return str(definition["cta_label"]) if definition is not None else "Open workflow"

    def _workflow_target_label(self, key: str) -> str:
        definition = self._WORKFLOW_DEFINITIONS.get(key)
        return str(definition["target_label"]) if definition is not None else "Workflow"

    def _workflow_impact_label(self, key: str) -> str:
        definition = self._WORKFLOW_DEFINITIONS.get(key)
        if definition is None:
            return "Open the next available workflow for this portfolio."
        return str(definition["impact"])

    def _parse_look_through_capability(
        self, payload: Any
    ) -> PortfolioAllocationLookThroughCapability | None:
        if not isinstance(payload, dict):
            return None
        requested_mode = self._optional_str(payload.get("requested_mode"))
        effective_mode = self._optional_str(payload.get("effective_mode"))
        if requested_mode is None or effective_mode is None:
            return None
        return PortfolioAllocationLookThroughCapability(
            requested_mode=requested_mode,
            effective_mode=effective_mode,
            applied=bool(payload.get("applied", False)),
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
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _optional_int(self, value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _resolve_portfolio_display_name(
        self, payload: dict[str, Any], *, fallback_portfolio_id: str
    ) -> str:
        return str(
            payload.get("portfolio_name")
            or payload.get("name")
            or payload.get("label")
            or payload.get("display_name")
            or fallback_portfolio_id
        )

    def _resolve_reporting_window(
        self,
        start_date: str | None,
        end_date: str | None,
        default_end_date: str | None = None,
    ) -> tuple[date, date]:
        window_end = (
            date.fromisoformat(end_date)
            if end_date
            else date.fromisoformat(default_end_date)
            if default_end_date
            else datetime.now(UTC).date()
        )
        window_start = (
            date.fromisoformat(start_date) if start_date else window_end - timedelta(days=29)
        )
        if window_start > window_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="portfolio reporting window start_date cannot be after end_date",
            )
        return window_start, window_end
