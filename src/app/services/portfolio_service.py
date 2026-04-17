import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.portfolio import (
    PortfolioActivityBucketSummary,
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
    PortfolioIncomePeriodSummary,
    PortfolioIncomeSummaryResponse,
    PortfolioIncomeTypeSummary,
    PortfolioInsight,
    PortfolioInsightsResponse,
    PortfolioLiquidityResponse,
    PortfolioMoneySummary,
    PortfolioOperationalReadiness,
    PortfolioPartialFailure,
    PortfolioPerformanceSummary,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioProfile,
    PortfolioProjectedCashflowResponse,
    PortfolioReadinessBucket,
    PortfolioReadinessIndicator,
    PortfolioReadinessReason,
    PortfolioReadinessResponse,
    PortfolioRebalanceSummary,
    PortfolioSummary,
    PortfolioTopPosition,
    PortfolioTransactionLedgerResponse,
    PortfolioTransactionView,
    PortfolioWorkflowAction,
    PortfolioWorkflowLaunchCue,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceControlCapabilities,
    PortfolioWorkspaceHistoricalSnapshotCapability,
    PortfolioWorkspaceModuleCapability,
    PortfolioWorkspaceReportingCurrencyCapability,
    PortfolioWorkspaceResponse,
)
from app.precision_policy import (
    quantize_money,
    quantize_performance,
    quantize_price,
    quantize_quantity,
)
from app.services.async_ttl_cache import AsyncTtlCache


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
        lotus_core_query_client: LotusCoreQueryClient,
        analytics_client: LotusAnalyticsClient | None = None,
        dpm_client: DpmClient | None = None,
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

    async def _get_portfolio_transactions_result(
        self,
        portfolio_id: str,
        correlation_id: str,
        *,
        as_of_date: str | None,
        include_projected: bool,
        skip: int,
        limit: int,
        transaction_type: str | None,
        security_id: str | None,
        instrument_id: str | None,
        component_type: str | None,
        linked_transaction_group_id: str | None,
        fx_contract_id: str | None,
        swap_event_id: str | None,
        near_leg_group_id: str | None,
        far_leg_group_id: str | None,
        sort_by: str,
        sort_order: str,
        start_date: str | None,
        end_date: str | None,
        reporting_currency: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_cached_upstream_result(
            (
                "transactions",
                portfolio_id,
                as_of_date,
                include_projected,
                skip,
                limit,
                transaction_type,
                security_id,
                instrument_id,
                component_type,
                linked_transaction_group_id,
                fx_contract_id,
                swap_event_id,
                near_leg_group_id,
                far_leg_group_id,
                sort_by,
                sort_order,
                start_date,
                end_date,
                reporting_currency,
            ),
            lambda: self._lotus_core_query_client.get_portfolio_transactions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order,
                transaction_type=transaction_type,
                security_id=security_id,
                instrument_id=instrument_id,
                component_type=component_type,
                linked_transaction_group_id=linked_transaction_group_id,
                fx_contract_id=fx_contract_id,
                swap_event_id=swap_event_id,
                near_leg_group_id=near_leg_group_id,
                far_leg_group_id=far_leg_group_id,
                start_date=start_date,
                end_date=end_date,
                reporting_currency=reporting_currency,
            ),
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
        (
            portfolio_result,
            aum_result,
            support_result,
            cashflow_result,
            cash_balance_result,
            readiness_result,
        ) = await asyncio.gather(
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
        performance_result, rebalance_result = await asyncio.gather(
            self._get_workspace_performance_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=effective_as_of_date,
            ),
            self._get_workspace_rebalance_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
        )
        portfolio_payload = self._require_payload(
            result=portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        self._raise_on_upstream_client_error(
            support_result,
            detail_prefix="lotus-core support overview rejected the request",
        )
        self._raise_on_upstream_client_error(
            readiness_result,
            detail_prefix="lotus-core portfolio readiness rejected the request",
        )
        portfolio = self._parse_portfolio_identity(portfolio_payload)
        profile = self._parse_portfolio_profile(portfolio_payload)
        warnings: list[str] = []
        partial_failures: list[PortfolioPartialFailure] = []
        summary = self._parse_summary(aum_result, cash_balance_result, warnings, partial_failures)
        cashflow_outlook = self._parse_cashflow(cashflow_result, warnings, partial_failures)
        performance = self._parse_workspace_performance(
            performance_result,
            warnings,
            partial_failures,
        )
        rebalance = self._parse_workspace_rebalance(
            rebalance_result,
            warnings,
            partial_failures,
        )
        operations = self._parse_operations(support_result, warnings, partial_failures)
        resolved_as_of_date = self._extract_resolved_as_of_date(aum_result) or effective_as_of_date
        return PortfolioWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=resolved_as_of_date,
            portfolio=portfolio,
            profile=profile,
            summary=summary,
            cashflow_outlook=cashflow_outlook,
            performance=performance,
            rebalance=rebalance,
            reporting=self._reporting_readiness(summary, readiness_result),
            operations=operations,
            control_capabilities=self._build_workspace_control_capabilities(
                portfolio=portfolio,
                profile=profile,
                requested_as_of_date=effective_as_of_date,
                effective_as_of_date=resolved_as_of_date,
                requested_reporting_currency=reporting_currency,
            ),
            workflow_cues=self._build_workflow_cues(portfolio_id),
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def get_portfolio_readiness(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioReadinessResponse:
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
        self._raise_on_upstream_client_error(
            source_readiness,
            detail_prefix="lotus-core portfolio readiness rejected the request",
        )
        source_payload = self._optional_payload(
            source_readiness,
            "lotus-core",
            "PORTFOLIO_SOURCE_READINESS_UNAVAILABLE",
            [],
            [],
        )
        indicators = self._build_source_readiness_indicators(
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
            holdings=self._parse_readiness_bucket((source_payload or {}).get("holdings")),
            pricing=self._parse_readiness_bucket((source_payload or {}).get("pricing")),
            transactions=self._parse_readiness_bucket((source_payload or {}).get("transactions")),
            reporting=self._parse_readiness_bucket((source_payload or {}).get("reporting")),
            blocking_reasons=self._parse_readiness_reasons(
                (source_payload or {}).get("blocking_reasons")
            ),
            indicators=indicators,
        )

    async def get_portfolio_insights(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioInsightsResponse:
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

        return PortfolioInsightsResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=workspace.as_of_date,
            insights=self._build_portfolio_insights(
                workspace=workspace,
                positions=positions.positions,
                top_positions=positions.top_positions,
                allocation_views=allocations.views,
                activity_summary=activity,
            ),
            exception_summaries=self._build_portfolio_exception_summaries(
                workspace=workspace,
                positions=positions.positions,
                allocation_views=allocations.views,
                transaction_total=transactions.total,
            ),
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
        portfolio_payload = self._require_payload(
            result=portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        cash_balances_payload = self._require_payload(
            result=cash_balances_result,
            unavailable_detail_prefix="lotus-core cash balances unavailable",
        )
        portfolio = self._parse_portfolio_identity(portfolio_payload)
        return PortfolioBookResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=positions.as_of_date,
            portfolio=portfolio,
            summary=positions.summary,
            cash_balances=self._parse_cash_balances(
                cash_balances_payload, positions.summary.assets_under_management_base
            ),
            allocation_views=allocations.views,
            top_positions=positions.top_positions,
            positions=positions.positions,
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
        (
            aum_result,
            cash_balances_result,
            cashflow_result,
        ) = await asyncio.gather(
            self._query_aum_result(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._query_cash_balances_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
            self._get_cashflow_projection_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=True,
                horizon_days=10,
            ),
        )
        aum_payload = self._require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        )
        cash_balances_payload = self._require_payload(
            result=cash_balances_result,
            unavailable_detail_prefix="lotus-core cash balances unavailable",
        )
        summary = self._parse_summary(aum_result, cash_balances_result, warnings, partial_failures)
        return PortfolioLiquidityResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=str(
                aum_payload.get("resolved_as_of_date") or as_of_date or datetime.now(UTC).date()
            ),
            portfolio_id=portfolio_id,
            summary=summary,
            cash_balances=self._parse_cash_balances(
                cash_balances_payload, summary.assets_under_management_base
            ),
            cashflow_outlook=self._parse_cashflow(cashflow_result, warnings, partial_failures),
            warnings=warnings,
            partial_failures=partial_failures,
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
        (
            aum_result,
            positions_result,
            allocation_result,
        ) = await asyncio.gather(
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
        aum_payload = self._require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        )
        allocation_payload = self._require_payload(
            result=allocation_result,
            unavailable_detail_prefix="lotus-core allocation unavailable",
        )
        positions_payload = self._require_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        )
        summary = self._parse_summary_from_positions(aum_result, positions_payload)
        return PortfolioAllocationResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=str(
                aum_payload.get("resolved_as_of_date") or as_of_date or datetime.now(UTC).date()
            ),
            reporting_currency=self._optional_str(allocation_payload.get("reporting_currency"))
            or reporting_currency,
            look_through=self._parse_look_through_capability(
                allocation_payload.get("look_through")
            ),
            summary=summary,
            views=self._parse_allocation_views(allocation_payload),
        )

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        reporting_currency: str | None = None,
    ) -> PortfolioPositionBookResponse:
        (
            aum_result,
            positions_result,
        ) = await asyncio.gather(
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
        positions = self._parse_positions(positions_payload)
        summary = self._parse_summary_from_positions(aum_result, positions_payload)
        return PortfolioPositionBookResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=str(
                aum_payload.get("resolved_as_of_date") or as_of_date or datetime.now(UTC).date()
            ),
            summary=summary,
            top_positions=self._build_top_positions(positions),
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
        status_code, payload = await self._get_portfolio_transactions_result(
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
        result_payload = self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core transactions unavailable",
        )
        transactions = [
            self._parse_transaction_view(item)
            for item in result_payload.get("transactions", [])
            if isinstance(item, dict)
        ]
        return PortfolioTransactionLedgerResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=(
                str(result_payload.get("as_of_date"))
                if result_payload.get("as_of_date")
                else as_of_date
            ),
            include_projected=include_projected,
            total=int(result_payload.get("total", len(transactions))),
            skip=int(result_payload.get("skip", skip)),
            limit=int(result_payload.get("limit", limit)),
            transactions=transactions,
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
            if self._transaction_date_in_range(
                transaction_date=self._transaction_date_value(item),
                start_date=window_start,
                end_date=window_end,
            )
        ]
        requested_totals, income_type_totals = self._summarize_income_rows(requested_window_rows)
        year_to_date_totals, income_type_ytd_totals = self._summarize_income_rows(year_to_date_rows)
        income_types = sorted(set(income_type_totals) | set(income_type_ytd_totals))
        return PortfolioIncomeSummaryResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            reporting_currency=resolved_reporting_currency or reporting_currency or "USD",
            window_start_date=window_start.isoformat(),
            window_end_date=window_end.isoformat(),
            totals_requested_window=self._build_income_period_summary(requested_totals),
            totals_year_to_date=self._build_income_period_summary(year_to_date_totals),
            income_types=[
                PortfolioIncomeTypeSummary(
                    income_type=income_type,
                    requested_window=self._build_income_period_summary(
                        income_type_totals.get(income_type, self._new_income_metric())
                    ),
                    year_to_date=self._build_income_period_summary(
                        income_type_ytd_totals.get(income_type, self._new_income_metric())
                    ),
                )
                for income_type in income_types
            ],
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
            if self._transaction_date_in_range(
                transaction_date=self._transaction_date_value(item),
                start_date=window_start,
                end_date=window_end,
            )
        ]
        requested_buckets = self._summarize_activity_rows(requested_window_rows)
        year_to_date_buckets = self._summarize_activity_rows(year_to_date_rows)
        bucket_names = list(
            dict.fromkeys([*requested_buckets.keys(), *year_to_date_buckets.keys()])
        )
        return PortfolioActivitySummaryResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            reporting_currency=resolved_reporting_currency or reporting_currency or "USD",
            window_start_date=window_start.isoformat(),
            window_end_date=window_end.isoformat(),
            buckets=[
                PortfolioActivityBucketSummary(
                    bucket=bucket,
                    requested_window=self._build_money_summary(
                        requested_buckets.get(bucket, self._new_flow_metric())
                    ),
                    year_to_date=self._build_money_summary(
                        year_to_date_buckets.get(bucket, self._new_flow_metric())
                    ),
                )
                for bucket in bucket_names
            ],
        )

    def _require_payload(
        self, result: tuple[int, dict[str, Any]], unavailable_detail_prefix: str
    ) -> dict[str, Any]:
        status_code, payload = result
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{unavailable_detail_prefix}: {payload}",
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
            raise HTTPException(status_code=status_code, detail=f"{detail_prefix}: {payload}")

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

    def _parse_summary_from_positions(
        self,
        aum_result: tuple[int, dict[str, Any]],
        positions_payload: dict[str, Any],
    ) -> PortfolioSummary:
        aum_payload = self._require_payload(
            result=aum_result,
            unavailable_detail_prefix="lotus-core aum unavailable",
        )
        first_portfolio: dict[str, Any] = next(iter(aum_payload.get("portfolios", [])), {})
        total_aum = float(quantize_money(first_portfolio.get("aum_reporting_currency", 0)))
        cash_total, cash_balance_count = self._summarize_cash_positions(positions_payload)
        cash_weight = (
            float(quantize_performance((cash_total / total_aum) * 100)) if total_aum > 0 else 0.0
        )
        return PortfolioSummary(
            assets_under_management_base=total_aum,
            invested_market_value_base=float(quantize_money(total_aum - cash_total)),
            cash_market_value_base=cash_total,
            cash_weight_pct=cash_weight,
            position_count=int(first_portfolio.get("position_count", 0)),
            cash_balance_count=cash_balance_count,
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
        results_by_period = payload.get("results_by_period", payload.get("resultsByPeriod", {}))
        if not isinstance(results_by_period, dict):
            warnings.append("PORTFOLIO_PERFORMANCE_INVALID")
            return None
        period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period), None)
        if period_key is None:
            return None
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        portfolio_payload = period_payload.get("portfolio", {})
        if not isinstance(portfolio_payload, dict):
            return None
        summary_payload = portfolio_payload.get("summary", {})
        if not isinstance(summary_payload, dict):
            return None
        period_return_payload = summary_payload.get("period_return", {})
        if not isinstance(period_return_payload, dict):
            return None
        period_return = period_return_payload.get("base")
        try:
            return_pct = (
                float(quantize_performance(period_return)) if period_return is not None else None
            )
        except (TypeError, ValueError):
            return_pct = None
        return PortfolioPerformanceSummary(period=str(period_key), return_pct=return_pct)

    def _parse_workspace_rebalance(
        self,
        result: tuple[int, dict[str, Any]] | None,
        warnings: list[str],
        partial_failures: list[PortfolioPartialFailure],
    ) -> PortfolioRebalanceSummary | None:
        if result is None:
            return None
        payload = self._optional_payload(
            result,
            "lotus-manage",
            "PORTFOLIO_REBALANCE_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        if payload is None:
            return None
        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            return None
        latest = items[0]
        if not isinstance(latest, dict):
            return None
        return PortfolioRebalanceSummary(
            status=str(latest.get("status", "UNKNOWN")),
            last_run_at_utc=self._optional_str(latest.get("created_at")),
            last_rebalance_run_id=self._optional_str(latest.get("rebalance_run_id")),
        )

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

    def _parse_positions(self, payload: dict[str, Any]) -> list[PortfolioPositionView]:
        return [
            PortfolioPositionView(
                security_id=str(item.get("security_id", "")),
                instrument_name=str(item.get("instrument_name", "")),
                asset_class=self._optional_str(item.get("asset_class")),
                isin=self._optional_str(item.get("isin")),
                currency=self._optional_str(item.get("currency")),
                sector=self._optional_str(item.get("sector")),
                country_of_risk=self._optional_str(item.get("country_of_risk")),
                held_since_date=str(item.get("held_since_date"))
                if item.get("held_since_date")
                else None,
                quantity=float(quantize_quantity(item.get("quantity", 0))),
                market_price=float(quantize_price(item.get("valuation", {}).get("market_price", 0)))
                if item.get("valuation", {}).get("market_price") is not None
                else None,
                cost_basis_base=float(quantize_money(item.get("cost_basis", 0)))
                if item.get("cost_basis") is not None
                else None,
                cost_basis_local=float(quantize_money(item.get("cost_basis_local", 0)))
                if item.get("cost_basis_local") is not None
                else None,
                market_value_base=float(
                    quantize_money(
                        self._position_valuation_value(
                            item, "market_value_base", fallback_key="market_value"
                        )
                    )
                )
                if self._position_valuation_value(
                    item, "market_value_base", fallback_key="market_value"
                )
                is not None
                else None,
                market_value_local=float(
                    quantize_money(
                        self._position_valuation_value(
                            item, "market_value_local", fallback_key="market_value"
                        )
                    )
                )
                if self._position_valuation_value(
                    item, "market_value_local", fallback_key="market_value"
                )
                is not None
                else None,
                unrealized_gain_loss_base=float(
                    quantize_money(
                        self._position_valuation_value(
                            item, "unrealized_gain_loss_base", fallback_key="unrealized_gain_loss"
                        )
                    )
                )
                if self._position_valuation_value(
                    item, "unrealized_gain_loss_base", fallback_key="unrealized_gain_loss"
                )
                is not None
                else None,
                unrealized_gain_loss_local=float(
                    quantize_money(
                        self._position_valuation_value(
                            item,
                            "unrealized_gain_loss_local",
                            fallback_key="unrealized_gain_loss",
                        )
                    )
                )
                if self._position_valuation_value(
                    item, "unrealized_gain_loss_local", fallback_key="unrealized_gain_loss"
                )
                is not None
                else None,
                weight_pct=float(quantize_performance(float(item.get("weight", 0)) * 100))
                if item.get("weight") is not None
                else None,
                reprocessing_status=self._optional_str(item.get("reprocessing_status")),
            )
            for item in payload.get("positions", [])
            if isinstance(item, dict)
        ]

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

    def _position_valuation_value(
        self, item: dict[str, Any], primary_key: str, fallback_key: str | None = None
    ) -> Any:
        valuation = item.get("valuation", {})
        if not isinstance(valuation, dict):
            return None
        primary_value = valuation.get(primary_key)
        if primary_value is not None:
            return primary_value
        if fallback_key is not None:
            return valuation.get(fallback_key)
        return None

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

    def _summarize_cash_positions(self, payload: dict[str, Any]) -> tuple[float, int]:
        cash_total = 0.0
        cash_count = 0
        for item in payload.get("positions", []):
            if not isinstance(item, dict):
                continue
            asset_class = str(item.get("asset_class") or "").strip().upper()
            if asset_class != "CASH":
                continue
            market_value = self._position_valuation_value(
                item, "market_value_base", fallback_key="market_value"
            )
            cash_total += float(quantize_money(market_value or 0))
            cash_count += 1
        return float(quantize_money(cash_total)), cash_count

    def _build_top_positions(
        self, positions: list[PortfolioPositionView]
    ) -> list[PortfolioTopPosition]:
        ranked = sorted(positions, key=lambda row: row.market_value_base or 0.0, reverse=True)[:10]
        return [PortfolioTopPosition(**row.model_dump()) for row in ranked]

    def _parse_transaction_view(self, item: dict[str, Any]) -> PortfolioTransactionView:
        return PortfolioTransactionView(
            transaction_id=str(item.get("transaction_id", "")),
            transaction_date=str(item.get("transaction_date", "")),
            settlement_date=self._optional_str(item.get("settlement_date")),
            transaction_type=str(item.get("transaction_type", "")),
            component_type=self._optional_str(item.get("component_type")),
            security_id=str(item.get("security_id", "")),
            instrument_id=str(item.get("instrument_id", "")),
            quantity=float(quantize_quantity(item.get("quantity", 0))),
            price=float(quantize_price(item.get("price", 0)))
            if item.get("price") is not None
            else None,
            gross_amount=float(quantize_money(item.get("gross_transaction_amount", 0)))
            if item.get("gross_transaction_amount") is not None
            else None,
            currency=self._optional_str(item.get("currency")),
            net_cost_base=float(quantize_money(item.get("net_cost", 0)))
            if item.get("net_cost") is not None
            else None,
            realized_gain_loss_base=float(quantize_money(item.get("realized_gain_loss", 0)))
            if item.get("realized_gain_loss") is not None
            else None,
            settlement_status=self._optional_str(item.get("settlement_status")),
            source_system=self._optional_str(item.get("source_system")),
            cash_entry_mode=self._optional_str(item.get("cash_entry_mode")),
            economic_event_id=self._optional_str(item.get("economic_event_id")),
            linked_transaction_group_id=self._optional_str(item.get("linked_transaction_group_id")),
            fx_contract_id=self._optional_str(item.get("fx_contract_id")),
            swap_event_id=self._optional_str(item.get("swap_event_id")),
            near_leg_group_id=self._optional_str(item.get("near_leg_group_id")),
            far_leg_group_id=self._optional_str(item.get("far_leg_group_id")),
        )

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
            status_code, payload = await self._get_portfolio_transactions_result(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=False,
                skip=skip,
                limit=page_size,
                transaction_type=None,
                security_id=None,
                instrument_id=None,
                component_type=None,
                linked_transaction_group_id=None,
                fx_contract_id=None,
                swap_event_id=None,
                near_leg_group_id=None,
                far_leg_group_id=None,
                sort_by="transaction_date",
                sort_order="asc",
                start_date=start_date,
                end_date=end_date,
                reporting_currency=reporting_currency,
            )
            result_payload = self._require_payload(
                result=(status_code, payload),
                unavailable_detail_prefix="lotus-core transactions unavailable",
            )
            if resolved_reporting_currency is None:
                resolved_reporting_currency = self._optional_str(
                    result_payload.get("reporting_currency")
                )
            page_rows = [
                item for item in result_payload.get("transactions", []) if isinstance(item, dict)
            ]
            rows.extend(page_rows)
            total = int(result_payload.get("total", len(page_rows)))
            skip += len(page_rows)
            if not page_rows or skip >= total:
                break

        return resolved_reporting_currency, rows

    def _summarize_income_rows(
        self,
        rows: list[dict[str, Any]],
    ) -> tuple[dict[str, float | int], dict[str, dict[str, float | int]]]:
        totals = self._new_income_metric()
        by_income_type: dict[str, dict[str, float | int]] = {}
        for row in rows:
            income_type = str(row.get("transaction_type") or "").strip().upper()
            if income_type not in {"DIVIDEND", "INTEREST"}:
                continue
            bucket = by_income_type.setdefault(income_type, self._new_income_metric())
            self._accumulate_income_metric(totals, row)
            self._accumulate_income_metric(bucket, row)
        return totals, by_income_type

    def _summarize_activity_rows(
        self, rows: list[dict[str, Any]]
    ) -> dict[str, dict[str, float | int]]:
        buckets: dict[str, dict[str, float | int]] = {}
        for row in rows:
            transaction_type = str(row.get("transaction_type") or "").strip().upper()
            bucket_name = self._activity_bucket_name(transaction_type)
            if bucket_name is not None:
                bucket = buckets.setdefault(bucket_name, self._new_flow_metric())
                self._accumulate_flow_metric(
                    bucket,
                    portfolio_amount=self._activity_portfolio_amount(row),
                    reporting_amount=self._activity_reporting_amount(row),
                )
            withholding_portfolio = self._absolute_money(row.get("withholding_tax_amount"))
            withholding_reporting = self._absolute_money(
                row.get("withholding_tax_amount_reporting_currency")
            )
            if withholding_portfolio > 0 or withholding_reporting > 0:
                tax_bucket = buckets.setdefault("TAXES", self._new_flow_metric())
                self._accumulate_flow_metric(
                    tax_bucket,
                    portfolio_amount=withholding_portfolio,
                    reporting_amount=withholding_reporting,
                )
        return buckets

    def _new_income_metric(self) -> dict[str, float | int]:
        return {
            "transaction_count": 0,
            "gross_amount_portfolio_currency": 0.0,
            "gross_amount_reporting_currency": 0.0,
            "withholding_tax_portfolio_currency": 0.0,
            "withholding_tax_reporting_currency": 0.0,
            "other_deductions_portfolio_currency": 0.0,
            "other_deductions_reporting_currency": 0.0,
            "net_amount_portfolio_currency": 0.0,
            "net_amount_reporting_currency": 0.0,
        }

    def _new_flow_metric(self) -> dict[str, float | int]:
        return {
            "transaction_count": 0,
            "amount_portfolio_currency": 0.0,
            "amount_reporting_currency": 0.0,
        }

    def _accumulate_income_metric(
        self,
        accumulator: dict[str, float | int],
        row: dict[str, Any],
    ) -> None:
        accumulator["transaction_count"] = int(accumulator["transaction_count"]) + 1
        accumulator["gross_amount_portfolio_currency"] = float(
            accumulator["gross_amount_portfolio_currency"]
        ) + self._absolute_money(row.get("gross_transaction_amount"))
        accumulator["gross_amount_reporting_currency"] = float(
            accumulator["gross_amount_reporting_currency"]
        ) + self._reporting_money(
            row,
            reporting_key="gross_transaction_amount_reporting_currency",
            portfolio_key="gross_transaction_amount",
        )
        accumulator["withholding_tax_portfolio_currency"] = float(
            accumulator["withholding_tax_portfolio_currency"]
        ) + self._absolute_money(row.get("withholding_tax_amount"))
        accumulator["withholding_tax_reporting_currency"] = float(
            accumulator["withholding_tax_reporting_currency"]
        ) + self._reporting_money(
            row,
            reporting_key="withholding_tax_amount_reporting_currency",
            portfolio_key="withholding_tax_amount",
        )
        accumulator["other_deductions_portfolio_currency"] = float(
            accumulator["other_deductions_portfolio_currency"]
        ) + self._absolute_money(row.get("other_interest_deductions_amount"))
        accumulator["other_deductions_reporting_currency"] = float(
            accumulator["other_deductions_reporting_currency"]
        ) + self._reporting_money(
            row,
            reporting_key="other_interest_deductions_amount_reporting_currency",
            portfolio_key="other_interest_deductions_amount",
        )
        accumulator["net_amount_portfolio_currency"] = float(
            accumulator["net_amount_portfolio_currency"]
        ) + self._income_net_portfolio_amount(row)
        accumulator["net_amount_reporting_currency"] = float(
            accumulator["net_amount_reporting_currency"]
        ) + self._income_net_reporting_amount(row)

    def _accumulate_flow_metric(
        self,
        accumulator: dict[str, float | int],
        *,
        portfolio_amount: float,
        reporting_amount: float,
    ) -> None:
        accumulator["transaction_count"] = int(accumulator["transaction_count"]) + 1
        accumulator["amount_portfolio_currency"] = (
            float(accumulator["amount_portfolio_currency"]) + portfolio_amount
        )
        accumulator["amount_reporting_currency"] = (
            float(accumulator["amount_reporting_currency"]) + reporting_amount
        )

    def _build_income_period_summary(
        self,
        payload: dict[str, float | int],
    ) -> PortfolioIncomePeriodSummary:
        return self._parse_income_period_summary(payload)

    def _build_money_summary(self, payload: dict[str, float | int]) -> PortfolioMoneySummary:
        return self._parse_money_summary(payload)

    def _activity_bucket_name(self, transaction_type: str) -> str | None:
        if transaction_type in {"DEPOSIT", "TRANSFER_IN"}:
            return "INFLOWS"
        if transaction_type in {"WITHDRAWAL", "TRANSFER_OUT"}:
            return "OUTFLOWS"
        if transaction_type == "FEE":
            return "FEES"
        if transaction_type == "TAX":
            return "TAXES"
        return None

    def _activity_portfolio_amount(self, row: dict[str, Any]) -> float:
        if str(row.get("transaction_type") or "").strip().upper() == "FEE":
            return self._absolute_money(row.get("gross_transaction_amount")) + self._absolute_money(
                row.get("trade_fee")
            )
        return self._absolute_money(row.get("gross_transaction_amount"))

    def _activity_reporting_amount(self, row: dict[str, Any]) -> float:
        if str(row.get("transaction_type") or "").strip().upper() == "FEE":
            return self._reporting_money(
                row,
                reporting_key="gross_transaction_amount_reporting_currency",
                portfolio_key="gross_transaction_amount",
            ) + self._reporting_money(
                row,
                reporting_key="trade_fee_reporting_currency",
                portfolio_key="trade_fee",
            )
        return self._reporting_money(
            row,
            reporting_key="gross_transaction_amount_reporting_currency",
            portfolio_key="gross_transaction_amount",
        )

    def _income_net_portfolio_amount(self, row: dict[str, Any]) -> float:
        if (
            str(row.get("transaction_type") or "").strip().upper() == "INTEREST"
            and row.get("net_interest_amount") is not None
        ):
            return self._absolute_money(row.get("net_interest_amount"))
        gross = self._absolute_money(row.get("gross_transaction_amount"))
        withholding = self._absolute_money(row.get("withholding_tax_amount"))
        other_deductions = self._absolute_money(row.get("other_interest_deductions_amount"))
        trade_fee = self._absolute_money(row.get("trade_fee"))
        return float(quantize_money(gross - withholding - other_deductions - trade_fee))

    def _income_net_reporting_amount(self, row: dict[str, Any]) -> float:
        if (
            str(row.get("transaction_type") or "").strip().upper() == "INTEREST"
            and row.get("net_interest_amount_reporting_currency") is not None
        ):
            return self._absolute_money(row.get("net_interest_amount_reporting_currency"))
        gross = self._reporting_money(
            row,
            reporting_key="gross_transaction_amount_reporting_currency",
            portfolio_key="gross_transaction_amount",
        )
        withholding = self._reporting_money(
            row,
            reporting_key="withholding_tax_amount_reporting_currency",
            portfolio_key="withholding_tax_amount",
        )
        other_deductions = self._reporting_money(
            row,
            reporting_key="other_interest_deductions_amount_reporting_currency",
            portfolio_key="other_interest_deductions_amount",
        )
        trade_fee = self._reporting_money(
            row,
            reporting_key="trade_fee_reporting_currency",
            portfolio_key="trade_fee",
        )
        return float(quantize_money(gross - withholding - other_deductions - trade_fee))

    def _reporting_money(
        self,
        row: dict[str, Any],
        *,
        reporting_key: str,
        portfolio_key: str,
    ) -> float:
        if row.get(reporting_key) is not None:
            return self._absolute_money(row.get(reporting_key))
        return self._absolute_money(row.get(portfolio_key))

    def _absolute_money(self, value: Any) -> float:
        if value is None:
            return 0.0
        return float(quantize_money(abs(float(value))))

    def _transaction_date_value(self, item: dict[str, Any]) -> date | None:
        raw_value = self._optional_str(item.get("transaction_date"))
        if raw_value is None:
            return None
        try:
            return date.fromisoformat(raw_value[:10])
        except ValueError:
            return None

    def _transaction_date_in_range(
        self,
        *,
        transaction_date: date | None,
        start_date: date,
        end_date: date,
    ) -> bool:
        if transaction_date is None:
            return False
        return start_date <= transaction_date <= end_date

    def _parse_income_period_summary(
        self,
        payload: dict[str, Any],
    ) -> PortfolioIncomePeriodSummary:
        return PortfolioIncomePeriodSummary(
            gross=self._parse_money_summary(
                payload,
                portfolio_key="gross_amount_portfolio_currency",
                reporting_key="gross_amount_reporting_currency",
            ),
            withholding_tax=self._parse_money_summary(
                payload,
                portfolio_key="withholding_tax_portfolio_currency",
                reporting_key="withholding_tax_reporting_currency",
            ),
            other_deductions=self._parse_money_summary(
                payload,
                portfolio_key="other_deductions_portfolio_currency",
                reporting_key="other_deductions_reporting_currency",
            ),
            net=self._parse_money_summary(
                payload,
                portfolio_key="net_amount_portfolio_currency",
                reporting_key="net_amount_reporting_currency",
            ),
        )

    def _parse_money_summary(
        self,
        payload: dict[str, Any],
        *,
        portfolio_key: str = "amount_portfolio_currency",
        reporting_key: str = "amount_reporting_currency",
    ) -> PortfolioMoneySummary:
        return PortfolioMoneySummary(
            portfolio_currency_amount=(
                float(quantize_money(payload.get(portfolio_key, 0)))
                if payload.get(portfolio_key) is not None
                else None
            ),
            reporting_currency_amount=float(quantize_money(payload.get(reporting_key, 0))),
            transaction_count=int(payload.get("transaction_count", 0)),
        )

    def _reporting_readiness(
        self,
        summary: PortfolioSummary,
        readiness_result: tuple[int, dict[str, Any]] | None = None,
    ):
        from app.contracts.portfolio import PortfolioReportingReadiness

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

        return [
            PortfolioReadinessIndicator(
                key="holdings",
                label="Holdings",
                status=holdings_status,
                href="#portfolio-drilldown" if detailed_view else "#portfolio-insights",
            ),
            PortfolioReadinessIndicator(
                key="pricing",
                label="Pricing",
                status=pricing_status,
                href="#portfolio-attention",
            ),
            PortfolioReadinessIndicator(
                key="transactions",
                label="Transactions",
                status=transactions_status,
                href="#portfolio-drilldown" if detailed_view else "#portfolio-insights",
            ),
            PortfolioReadinessIndicator(
                key="reporting",
                label="Reporting",
                status=reporting_status,
                href="#portfolio-health",
            ),
        ]

    def _build_portfolio_exception_summaries(
        self,
        *,
        workspace: PortfolioWorkspaceResponse,
        positions: list[PortfolioPositionView],
        allocation_views: list[PortfolioAllocationView],
        transaction_total: int,
    ) -> list[PortfolioExceptionSummary]:
        exceptions: list[PortfolioExceptionSummary] = []
        holdings_status = self._holdings_readiness_status(
            position_count=workspace.summary.position_count,
            positions=positions,
        )
        pricing_status = self._pricing_readiness_status(
            positions=positions,
            allocation_views=allocation_views,
        )
        transaction_status = self._transactions_readiness_status(
            transaction_total=transaction_total,
            operations=workspace.operations,
        )
        reporting_status = self._reporting_status_label(
            workspace.reporting.status,
            workspace.reporting.row_count,
        )

        if holdings_status != "Ready":
            exceptions.append(
                PortfolioExceptionSummary(
                    key="holdings",
                    title=(
                        "Holdings coverage incomplete"
                        if holdings_status == "Partial"
                        else "Missing holdings"
                    ),
                    detail=(
                        "The holdings inventory is only partially available for this book."
                        if holdings_status == "Partial"
                        else "No positions are currently booked for this portfolio."
                    ),
                    tone="warn" if holdings_status == "Partial" else "danger",
                    href="#portfolio-drilldown",
                )
            )

        if pricing_status != "Ready":
            exceptions.append(
                PortfolioExceptionSummary(
                    key="pricing",
                    title=(
                        "Pricing coverage incomplete"
                        if pricing_status == "Partial"
                        else "No priced positions"
                    ),
                    detail=(
                        "Some holdings lack complete valuation coverage."
                        if pricing_status == "Partial"
                        else "Valuation cannot run until priced positions are available."
                    ),
                    tone="warn" if pricing_status == "Partial" else "danger",
                    href="#portfolio-attention",
                )
            )

        if transaction_status != "Ready":
            exceptions.append(
                PortfolioExceptionSummary(
                    key="transactions",
                    title=(
                        "Transaction history incomplete"
                        if transaction_status == "Partial"
                        else "Empty transaction history"
                    ),
                    detail=(
                        "Booked transaction history is present but not fully "
                        "available in the current view."
                        if transaction_status == "Partial"
                        else "No funding, trading, or cash activity has been recorded yet."
                    ),
                    tone="warn" if transaction_status == "Partial" else "danger",
                    href="#portfolio-drilldown",
                )
            )

        if reporting_status != "Ready":
            exceptions.append(
                PortfolioExceptionSummary(
                    key="reporting",
                    title=(
                        "Reporting output incomplete"
                        if reporting_status == "Partial"
                        else "Reporting output unavailable"
                        if reporting_status == "Empty"
                        else "Reporting output missing"
                    ),
                    detail=(
                        "Reporting output exists, but the current book is not fully reportable."
                        if reporting_status == "Partial"
                        else "Reporting has not produced any rows for this portfolio yet."
                        if reporting_status == "Empty"
                        else "Reporting coverage is not yet available for this portfolio."
                    ),
                    tone="warn" if reporting_status in {"Partial", "Empty"} else "danger",
                    href="#portfolio-health",
                )
            )

        if workspace.operations and workspace.operations.controls_blocking:
            exceptions.append(
                PortfolioExceptionSummary(
                    key="controls_blocking",
                    title="Blocking controls active",
                    detail=(
                        "Operational controls are currently preventing publication "
                        "or downstream processing."
                    ),
                    tone="danger",
                    href="#portfolio-attention",
                )
            )

        for failure in workspace.partial_failures:
            exceptions.append(
                PortfolioExceptionSummary(
                    key=f"partial_failure_{failure.error_code}",
                    title=failure.error_code.replace("_", " "),
                    detail=failure.detail,
                    tone="warn",
                    href="#portfolio-attention",
                )
            )

        return exceptions

    def _build_portfolio_insights(
        self,
        *,
        workspace: PortfolioWorkspaceResponse,
        positions: list[PortfolioPositionView],
        top_positions: list[PortfolioTopPosition],
        allocation_views: list[PortfolioAllocationView],
        activity_summary: PortfolioActivitySummaryResponse,
    ) -> list[PortfolioInsight]:
        insights: list[PortfolioInsight] = []
        pricing_status = self._pricing_readiness_status(
            positions=positions,
            allocation_views=allocation_views,
        )
        reporting_status = self._reporting_status_label(
            workspace.reporting.status,
            workspace.reporting.row_count,
        )
        max_position_weight = self._max_position_weight(
            positions=positions,
            top_positions=top_positions,
        )
        requested_window_activity = self._requested_window_activity_amount(activity_summary)

        if not positions:
            insights.append(
                PortfolioInsight(
                    key="no-holdings-booked",
                    title="No holdings booked",
                    detail=(
                        "Book the first position to activate holdings, allocation, "
                        "and valuation views."
                    ),
                    severity="critical",
                    href="#portfolio-drilldown",
                )
            )

        if not self._has_cash_funding_evidence(
            summary=workspace.summary,
            activity_summary=activity_summary,
        ):
            insights.append(
                PortfolioInsight(
                    key="no-cash-funding",
                    title="No cash funding recorded",
                    detail=(
                        "Add opening cash or a subscription so the portfolio can "
                        "be funded and invested."
                    ),
                    severity="critical",
                    href="#portfolio-insights",
                )
            )

        if pricing_status != "Ready":
            insights.append(
                PortfolioInsight(
                    key="pricing-not-published",
                    title="Pricing not yet published",
                    detail="Publish prices to complete valuation and unlock reliable reporting.",
                    severity="warning",
                    href="#portfolio-attention",
                )
            )

        if reporting_status != "Ready":
            insights.append(
                PortfolioInsight(
                    key="reporting-unavailable",
                    title="Reporting cannot be generated yet",
                    detail=(
                        "Reporting remains blocked until book coverage and valuation are complete."
                    ),
                    severity="warning",
                    href="#portfolio-health",
                )
            )

        if max_position_weight >= 20:
            insights.append(
                PortfolioInsight(
                    key="equity-concentration-high",
                    title="Large position dominates portfolio risk",
                    detail=(
                        "One holding has become large enough to dominate current "
                        "portfolio concentration. Open Risk to review concentration pressure."
                    ),
                    severity="warning",
                    href=f"/risk?portfolioId={workspace.portfolio.portfolio_id}",
                )
            )

        if (workspace.summary.cash_weight_pct or 0) >= 15:
            insights.append(
                PortfolioInsight(
                    key="cash-above-target",
                    title="Cash exceeds target allocation",
                    detail="Available cash is elevated relative to invested assets.",
                    severity="info",
                    href="#portfolio-insights",
                )
            )

        if requested_window_activity < 0:
            insights.append(
                PortfolioInsight(
                    key="net-outflows-window",
                    title="Net outflows in last 30 days",
                    detail="Recent activity is net negative over the selected reporting window.",
                    severity="warning",
                    href="#portfolio-changes",
                )
            )

        return insights

    def _max_position_weight(
        self,
        *,
        positions: list[PortfolioPositionView],
        top_positions: list[PortfolioTopPosition],
    ) -> float:
        weighted_positions = [
            *(position.weight_pct or 0 for position in top_positions),
            *(position.weight_pct or 0 for position in positions),
        ]
        return max(weighted_positions, default=0)

    def _has_cash_funding_evidence(
        self,
        *,
        summary: PortfolioSummary,
        activity_summary: PortfolioActivitySummaryResponse,
    ) -> bool:
        if summary.cash_balance_count > 0:
            return True
        if summary.cash_market_value_base > 0:
            return True

        inflow_bucket = next(
            (bucket for bucket in activity_summary.buckets if bucket.bucket.upper() == "INFLOWS"),
            None,
        )
        if inflow_bucket is None:
            return False
        if inflow_bucket.requested_window.transaction_count > 0:
            return True
        return inflow_bucket.requested_window.reporting_currency_amount > 0

    def _build_workflow_actions(
        self,
        *,
        portfolio_id: str,
        summary: PortfolioSummary,
        operations: PortfolioOperationalReadiness | None,
        workflow_cues: list[PortfolioWorkflowLaunchCue],
        transaction_total: int,
    ) -> list[PortfolioWorkflowAction]:
        portfolio_operations_href = f"/workbench?portfolioId={portfolio_id}"
        is_empty_portfolio = (
            summary.position_count == 0
            and summary.cash_balance_count == 0
            and transaction_total == 0
        )

        if is_empty_portfolio:
            return [
                PortfolioWorkflowAction(
                    sequence=1,
                    title="Fund portfolio",
                    impact=(
                        "Create opening liquidity so balances, allocation, and readiness "
                        "checks become meaningful."
                    ),
                    target="Target: cash funding and opening balance setup",
                    href=portfolio_operations_href,
                    cta_label="Fund now",
                    recommended=True,
                ),
                PortfolioWorkflowAction(
                    sequence=2,
                    title="Book first trade",
                    impact="Activate the holdings book and create the first investable position.",
                    target="Target: transaction entry and execution workflow",
                    href=portfolio_operations_href,
                    cta_label="Book trade",
                    recommended=False,
                ),
                PortfolioWorkflowAction(
                    sequence=3,
                    title="Publish pricing",
                    impact="Enable valuation, allocation, and downstream reporting coverage.",
                    target="Target: pricing publication and valuation refresh",
                    href=portfolio_operations_href,
                    cta_label="Publish prices",
                    recommended=False,
                ),
                PortfolioWorkflowAction(
                    sequence=4,
                    title="Review holdings",
                    impact=(
                        "Confirm the funded book, position weights, and coverage after valuation."
                    ),
                    target="Target: holdings and allocation review",
                    href="#portfolio-insights",
                    cta_label="Open holdings",
                    recommended=False,
                ),
                PortfolioWorkflowAction(
                    sequence=5,
                    title="Open performance",
                    impact="Review return analytics once holdings are funded and valued.",
                    target="Target: performance workspace after valuation is available",
                    href=f"/performance?portfolioId={portfolio_id}",
                    cta_label="Open performance",
                    recommended=False,
                ),
            ]

        ordered_cues = sorted(
            self._supported_workflow_cues(self._dedupe_workflow_cues(workflow_cues)),
            key=lambda cue: self._workflow_order_rank(cue.key),
        )
        return [
            PortfolioWorkflowAction(
                sequence=index + 1,
                title=self._workflow_task_label(cue.key),
                impact=self._workflow_impact_label(cue.key),
                target=(
                    f"Target: {self._workflow_target_label(cue.key)} workflow for this portfolio"
                ),
                href=cue.href,
                cta_label=self._workflow_cta_label(cue.key),
                recommended=index == 0,
            )
            for index, cue in enumerate(ordered_cues)
        ]

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

    def _requested_window_activity_amount(
        self, activity_summary: PortfolioActivitySummaryResponse
    ) -> float:
        return float(
            sum(
                bucket.requested_window.reporting_currency_amount
                * (
                    1
                    if bucket.bucket.upper() == "INFLOWS"
                    else -1
                    if bucket.bucket.upper() in {"OUTFLOWS", "FEES", "TAXES"}
                    else 0
                )
                for bucket in activity_summary.buckets
            )
        )

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

    def _parse_readiness_bucket(self, payload: Any) -> PortfolioReadinessBucket | None:
        if not isinstance(payload, dict):
            return None
        status_value = self._optional_str(payload.get("status"))
        if status_value is None:
            return None
        return PortfolioReadinessBucket(
            status=self._map_source_readiness_status(status_value),
            reasons=self._parse_readiness_reasons(payload.get("reasons")),
        )

    def _parse_readiness_reasons(self, payload: Any) -> list[PortfolioReadinessReason]:
        if not isinstance(payload, list):
            return []
        reasons: list[PortfolioReadinessReason] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            code = self._optional_str(item.get("code"))
            if code is None:
                continue
            reasons.append(
                PortfolioReadinessReason(
                    code=code,
                    detail=self._optional_str(item.get("detail")),
                )
            )
        return reasons

    def _build_source_readiness_indicators(
        self, payload: dict[str, Any] | None, detailed_view: bool
    ) -> list[PortfolioReadinessIndicator]:
        if payload is None:
            return []
        return [
            PortfolioReadinessIndicator(
                key="holdings",
                label="Holdings",
                status=self._map_source_readiness_status(payload.get("holdings", {}).get("status")),
                href="#portfolio-drilldown" if detailed_view else "#portfolio-insights",
            ),
            PortfolioReadinessIndicator(
                key="pricing",
                label="Pricing",
                status=self._map_source_readiness_status(payload.get("pricing", {}).get("status")),
                href="#portfolio-attention",
            ),
            PortfolioReadinessIndicator(
                key="transactions",
                label="Transactions",
                status=self._map_source_readiness_status(
                    payload.get("transactions", {}).get("status")
                ),
                href="#portfolio-drilldown" if detailed_view else "#portfolio-insights",
            ),
            PortfolioReadinessIndicator(
                key="reporting",
                label="Reporting",
                status=self._map_source_readiness_status(
                    payload.get("reporting", {}).get("status")
                ),
                href="#portfolio-health",
            ),
        ]

    def _map_source_readiness_status(self, status_value: Any) -> str:
        normalized = str(status_value or "").strip().upper()
        mapping = {
            "READY": "Ready",
            "PENDING": "Pending",
            "BLOCKED": "Blocked",
            "FAILED": "Blocked",
            "EMPTY": "Empty",
        }
        return mapping.get(normalized, "Pending" if normalized else "Unknown")

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
        effective_reporting_currency = requested_reporting_currency or portfolio.base_currency
        supported_currencies: list[str] = []
        for currency in (portfolio.base_currency, effective_reporting_currency):
            if currency not in supported_currencies:
                supported_currencies.append(currency)

        return PortfolioWorkspaceControlCapabilities(
            historical_snapshots=PortfolioWorkspaceHistoricalSnapshotCapability(
                state="partial",
                reason=(
                    "Most portfolio modules honor as_of_date, but rebalance and performance "
                    "snapshot still follow separate control semantics."
                ),
                requested_as_of_date=requested_as_of_date,
                effective_as_of_date=effective_as_of_date,
                earliest_available_as_of_date=profile.open_date,
                latest_available_as_of_date=effective_as_of_date,
                module_capabilities=[
                    PortfolioWorkspaceModuleCapability(
                        module="workspace",
                        state="supported",
                        reason=(
                            "Workspace shell summary, cashflow, and readiness resolve the "
                            "selected as_of_date."
                        ),
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="book",
                        state="supported",
                        reason="Book accepts and honors as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="liquidity",
                        state="supported",
                        reason="Liquidity accepts and honors as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="allocations",
                        state="supported",
                        reason="Allocations accept and honor as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="positions",
                        state="supported",
                        reason="Positions accept and honor as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="transactions",
                        state="supported",
                        reason="Transactions accept and honor as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="income_summary",
                        state="supported",
                        reason="Income summary accepts and honors as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="activity_summary",
                        state="supported",
                        reason="Activity summary accepts and honors as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="readiness",
                        state="supported",
                        reason="Readiness accepts and honors as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="workflow",
                        state="supported",
                        reason="Workflow accepts and honors as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="insights",
                        state="supported",
                        reason="Insights accept and honor as_of_date directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="performance_snapshot",
                        state="partial",
                        reason=(
                            "Performance snapshot aligns through explicit report window controls "
                            "rather than a first-class as_of_date parameter."
                        ),
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="rebalance",
                        state="unsupported",
                        reason=(
                            "Rebalance shell summary is always sourced from the latest "
                            "available run."
                        ),
                    ),
                ],
            ),
            reporting_currency_restatement=PortfolioWorkspaceReportingCurrencyCapability(
                state="partial",
                reason=(
                    "Book-style holdings and transaction modules honor reporting_currency, but "
                    "workflow, readiness, and performance snapshot do not yet share that control."
                ),
                requested_reporting_currency=requested_reporting_currency,
                effective_reporting_currency=effective_reporting_currency,
                supported_currencies=supported_currencies,
                module_capabilities=[
                    PortfolioWorkspaceModuleCapability(
                        module="workspace",
                        state="partial",
                        reason=(
                            "Workspace shell summary honors reporting_currency for holdings and "
                            "cash, but not for every shell section."
                        ),
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="book",
                        state="supported",
                        reason="Book accepts and honors reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="liquidity",
                        state="supported",
                        reason="Liquidity accepts and honors reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="allocations",
                        state="supported",
                        reason="Allocations accept and honor reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="positions",
                        state="supported",
                        reason="Positions accept and honor reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="transactions",
                        state="supported",
                        reason="Transactions accept and honor reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="income_summary",
                        state="supported",
                        reason="Income summary accepts and honors reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="activity_summary",
                        state="supported",
                        reason="Activity summary accepts and honors reporting_currency directly.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="readiness",
                        state="unsupported",
                        reason="Readiness does not expose reporting_currency-aware semantics.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="workflow",
                        state="unsupported",
                        reason=(
                            "Workflow priorities do not expose reporting_currency-aware semantics."
                        ),
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="insights",
                        state="unsupported",
                        reason=(
                            "Insights do not currently expose reporting_currency-aware semantics."
                        ),
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="performance_snapshot",
                        state="unsupported",
                        reason="Performance snapshot does not expose reporting_currency.",
                    ),
                    PortfolioWorkspaceModuleCapability(
                        module="rebalance",
                        state="unsupported",
                        reason=(
                            "Rebalance shell summary does not expose reporting_currency-aware "
                            "state."
                        ),
                    ),
                ],
            ),
        )

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

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
