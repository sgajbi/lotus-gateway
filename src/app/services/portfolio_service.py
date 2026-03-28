import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.portfolio import (
    PortfolioActivityBucketSummary,
    PortfolioActivitySummaryResponse,
    PortfolioAllocationBucket,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioBookResponse,
    PortfolioCashBalance,
    PortfolioCashflowOutlook,
    PortfolioCashflowPoint,
    PortfolioCatalogItem,
    PortfolioCatalogResponse,
    PortfolioIdentity,
    PortfolioIncomePeriodSummary,
    PortfolioIncomeSummaryResponse,
    PortfolioIncomeTypeSummary,
    PortfolioLiquidityResponse,
    PortfolioMoneySummary,
    PortfolioOperationalReadiness,
    PortfolioPartialFailure,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioProfile,
    PortfolioReadinessIndicator,
    PortfolioReadinessResponse,
    PortfolioSummary,
    PortfolioTopPosition,
    PortfolioTransactionLedgerResponse,
    PortfolioTransactionView,
    PortfolioWorkflowAction,
    PortfolioWorkflowLaunchCue,
    PortfolioWorkflowResponse,
    PortfolioWorkspaceResponse,
)
from app.precision_policy import (
    quantize_money,
    quantize_performance,
    quantize_price,
    quantize_quantity,
)


class PortfolioService:
    def __init__(self, lotus_core_query_client: LotusCoreQueryClient):
        self._lotus_core_query_client = lotus_core_query_client

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
        self, portfolio_id: str, correlation_id: str
    ) -> PortfolioWorkspaceResponse:
        as_of_date = datetime.now(UTC).date().isoformat()
        (
            portfolio_result,
            aum_result,
            support_result,
            cashflow_result,
            cash_balance_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.query_assets_under_management(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
            ),
            self._lotus_core_query_client.get_support_overview(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_cashflow_projection(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=True,
                horizon_days=10,
            ),
            self._lotus_core_query_client.query_cash_balances(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
        )
        portfolio_payload = self._require_payload(
            result=portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        portfolio = self._parse_portfolio_identity(portfolio_payload)
        profile = self._parse_portfolio_profile(portfolio_payload)
        warnings: list[str] = []
        partial_failures: list[PortfolioPartialFailure] = []
        summary = self._parse_summary(aum_result, cash_balance_result, warnings, partial_failures)
        cashflow_outlook = self._parse_cashflow(cashflow_result, warnings, partial_failures)
        operations = self._parse_operations(support_result, warnings, partial_failures)
        return PortfolioWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=self._extract_resolved_as_of_date(aum_result) or as_of_date,
            portfolio=portfolio,
            profile=profile,
            summary=summary,
            cashflow_outlook=cashflow_outlook,
            reporting=self._reporting_readiness(summary),
            operations=operations,
            workflow_cues=self._build_workflow_cues(portfolio_id),
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def get_portfolio_readiness(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioReadinessResponse:
        workspace, positions, allocations, transactions = await asyncio.gather(
            self.get_portfolio_workspace(portfolio_id=portfolio_id, correlation_id=correlation_id),
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
            self.get_transaction_ledger(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=False,
                skip=0,
                limit=1,
            ),
        )
        indicators = self._build_readiness_indicators(
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
            indicators=indicators,
        )

    async def get_portfolio_workflow(
        self, portfolio_id: str, correlation_id: str, as_of_date: str | None
    ) -> PortfolioWorkflowResponse:
        workspace, transactions = await asyncio.gather(
            self.get_portfolio_workspace(portfolio_id=portfolio_id, correlation_id=correlation_id),
            self.get_transaction_ledger(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=False,
                skip=0,
                limit=1,
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

    async def get_portfolio_book(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
    ) -> PortfolioBookResponse:
        allocations = await self.get_portfolio_allocations(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        liquidity = await self.get_portfolio_liquidity(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        positions = await self.get_portfolio_positions(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
        )
        portfolio_payload = self._require_payload(
            result=await self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id, correlation_id=correlation_id
            ),
            unavailable_detail_prefix="lotus-core portfolio unavailable",
        )
        portfolio = self._parse_portfolio_identity(portfolio_payload)
        return PortfolioBookResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=positions.as_of_date,
            portfolio=portfolio,
            summary=positions.summary,
            cash_balances=liquidity.cash_balances,
            allocation_views=allocations.views,
            top_positions=positions.top_positions,
            positions=positions.positions,
        )

    async def get_portfolio_liquidity(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> PortfolioLiquidityResponse:
        warnings: list[str] = []
        partial_failures: list[PortfolioPartialFailure] = []
        (
            aum_result,
            cash_balances_result,
            cashflow_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.query_assets_under_management(
                correlation_id=correlation_id, portfolio_id=portfolio_id, as_of_date=as_of_date
            ),
            self._lotus_core_query_client.query_cash_balances(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._lotus_core_query_client.get_cashflow_projection(
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

    async def get_portfolio_allocations(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
    ) -> PortfolioAllocationResponse:
        (
            aum_result,
            cash_balances_result,
            allocation_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.query_assets_under_management(
                correlation_id=correlation_id, portfolio_id=portfolio_id, as_of_date=as_of_date
            ),
            self._lotus_core_query_client.query_cash_balances(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._lotus_core_query_client.query_asset_allocation(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                dimensions=["asset_class", "currency", "sector"],
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
        summary = self._parse_summary(aum_result, cash_balances_result, [], [])
        return PortfolioAllocationResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=str(
                aum_payload.get("resolved_as_of_date") or as_of_date or datetime.now(UTC).date()
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
    ) -> PortfolioPositionBookResponse:
        (
            aum_result,
            cash_balances_result,
            positions_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.query_assets_under_management(
                correlation_id=correlation_id, portfolio_id=portfolio_id, as_of_date=as_of_date
            ),
            self._lotus_core_query_client.query_cash_balances(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
            ),
            self._lotus_core_query_client.get_portfolio_positions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                include_projected=include_projected,
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
        summary = self._parse_summary(aum_result, cash_balances_result, [], [])
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
    ) -> PortfolioTransactionLedgerResponse:
        status_code, payload = await self._lotus_core_query_client.get_portfolio_transactions(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            skip=skip,
            limit=limit,
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
        start_date: str | None,
        end_date: str | None,
    ) -> PortfolioIncomeSummaryResponse:
        window_start, window_end = self._resolve_reporting_window(start_date, end_date)
        status_code, payload = await self._lotus_core_query_client.query_income_summary(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            start_date=window_start.isoformat(),
            end_date=window_end.isoformat(),
        )
        result_payload = self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core income summary unavailable",
        )
        portfolio_payload = next(iter(result_payload.get("portfolios", [])), {})
        income_types = [
            PortfolioIncomeTypeSummary(
                income_type=str(item.get("income_type", "")),
                requested_window=self._parse_income_period_summary(
                    item.get("requested_window", {}),
                ),
                year_to_date=self._parse_income_period_summary(item.get("year_to_date", {})),
            )
            for item in portfolio_payload.get("income_types", [])
            if isinstance(item, dict)
        ]
        return PortfolioIncomeSummaryResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            reporting_currency=str(result_payload.get("reporting_currency", "USD")),
            window_start_date=window_start.isoformat(),
            window_end_date=window_end.isoformat(),
            totals_requested_window=self._parse_income_period_summary(
                result_payload.get("totals", {}).get("requested_window", {})
            ),
            totals_year_to_date=self._parse_income_period_summary(
                result_payload.get("totals", {}).get("year_to_date", {})
            ),
            income_types=income_types,
        )

    async def get_activity_summary(
        self,
        portfolio_id: str,
        correlation_id: str,
        start_date: str | None,
        end_date: str | None,
    ) -> PortfolioActivitySummaryResponse:
        window_start, window_end = self._resolve_reporting_window(start_date, end_date)
        status_code, payload = await self._lotus_core_query_client.query_activity_summary(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            start_date=window_start.isoformat(),
            end_date=window_end.isoformat(),
        )
        result_payload = self._require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core activity summary unavailable",
        )
        return PortfolioActivitySummaryResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            reporting_currency=str(result_payload.get("reporting_currency", "USD")),
            window_start_date=window_start.isoformat(),
            window_end_date=window_end.isoformat(),
            buckets=[
                PortfolioActivityBucketSummary(
                    bucket=str(item.get("bucket", "")),
                    requested_window=self._parse_money_summary(item.get("requested_window", {})),
                    year_to_date=self._parse_money_summary(item.get("year_to_date", {})),
                )
                for item in result_payload.get("totals", {}).get("buckets", [])
                if isinstance(item, dict)
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

    def _parse_catalog_item(self, item: dict[str, Any]) -> PortfolioCatalogItem:
        portfolio_id = str(item.get("portfolio_id", "")).strip()
        return PortfolioCatalogItem(
            portfolio_id=portfolio_id,
            display_name=portfolio_id,
            base_currency=str(item.get("base_currency", "USD")),
            client_id=self._optional_str(item.get("client_id")),
            booking_center_code=self._optional_str(item.get("booking_center_code")),
            portfolio_type=self._optional_str(item.get("portfolio_type")),
            status=self._optional_str(item.get("status")),
        )

    def _parse_portfolio_identity(self, payload: dict[str, Any]) -> PortfolioIdentity:
        return PortfolioIdentity(
            portfolio_id=str(payload.get("portfolio_id", "")),
            display_name=str(payload.get("portfolio_id", "")),
            client_id=self._optional_str(payload.get("client_id")),
            base_currency=str(payload.get("base_currency", "USD")),
            booking_center_code=self._optional_str(payload.get("booking_center_code")),
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
        first_portfolio = next(iter(aum_payload.get("portfolios", [])), {})
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
                    quantize_money(item.get("valuation", {}).get("market_value_base", 0))
                )
                if item.get("valuation", {}).get("market_value_base") is not None
                else None,
                market_value_local=float(
                    quantize_money(item.get("valuation", {}).get("market_value_local", 0))
                )
                if item.get("valuation", {}).get("market_value_local") is not None
                else None,
                unrealized_gain_loss_base=float(
                    quantize_money(item.get("valuation", {}).get("unrealized_gain_loss", 0))
                )
                if item.get("valuation", {}).get("unrealized_gain_loss") is not None
                else None,
                unrealized_gain_loss_local=float(
                    quantize_money(item.get("valuation", {}).get("unrealized_gain_loss_local", 0))
                )
                if item.get("valuation", {}).get("unrealized_gain_loss_local") is not None
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

    def _build_top_positions(
        self, positions: list[PortfolioPositionView]
    ) -> list[PortfolioTopPosition]:
        ranked = sorted(positions, key=lambda row: row.market_value_base or 0.0, reverse=True)[:10]
        return [PortfolioTopPosition(**row.model_dump()) for row in ranked]

    def _parse_transaction_view(self, item: dict[str, Any]) -> PortfolioTransactionView:
        return PortfolioTransactionView(
            transaction_id=str(item.get("transaction_id", "")),
            transaction_date=str(item.get("transaction_date", "")),
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
        )

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

    def _reporting_readiness(self, summary: PortfolioSummary):
        from app.contracts.portfolio import PortfolioReportingReadiness

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
                        "Confirm the funded book, position weights, and coverage after "
                        "valuation."
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
                    href="/performance",
                    cta_label="Open performance",
                    recommended=False,
                ),
            ]

        ordered_cues = sorted(
            self._dedupe_workflow_cues(workflow_cues),
            key=lambda cue: self._workflow_order_rank(cue.key),
        )
        return [
            PortfolioWorkflowAction(
                sequence=index + 1,
                title=self._workflow_task_label(cue.key),
                impact=self._workflow_impact_label(cue.key),
                target=f"Target: {cue.label} workflow for this portfolio",
                href=cue.href,
                cta_label=cue.label,
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

    def _workflow_order_rank(self, key: str) -> int:
        order = {
            "performance": 0,
            "holdings": 1,
            "transactions": 2,
            "risk": 3,
            "proposal": 4,
        }
        return order.get(key, 99)

    def _workflow_task_label(self, key: str) -> str:
        mapping = {
            "performance": "Review performance",
            "holdings": "Review holdings",
            "transactions": "Review transactions",
            "risk": "Review suitability",
            "proposal": "Prepare recommendation",
        }
        return mapping.get(key, "Open workflow")

    def _workflow_impact_label(self, key: str) -> str:
        mapping = {
            "performance": (
                "Review portfolio return, benchmark context, and contribution once the book "
                "is valued."
            ),
            "holdings": (
                "Confirm funded positions, valuations, and portfolio weights before client "
                "review."
            ),
            "transactions": (
                "Inspect recent funding, trading, and cash activity affecting the book."
            ),
            "risk": (
                "Validate suitability, exposure, and mandate fit before the next client "
                "action."
            ),
            "proposal": "Prepare the next recommended portfolio action or client proposal.",
        }
        return mapping.get(key, "Open the next available workflow for this portfolio.")

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
                detail=str(payload),
            )
        )
        return None

    def _extract_resolved_as_of_date(self, result: tuple[int, dict[str, Any]]) -> str | None:
        payload = self._optional_payload(result, "lotus-core", "IGNORED", [], [])
        return (
            str(payload.get("resolved_as_of_date"))
            if payload and payload.get("resolved_as_of_date")
            else None
        )

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _resolve_reporting_window(
        self,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[date, date]:
        window_end = date.fromisoformat(end_date) if end_date else datetime.now(UTC).date()
        window_start = (
            date.fromisoformat(start_date) if start_date else window_end - timedelta(days=29)
        )
        if window_start > window_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="portfolio reporting window start_date cannot be after end_date",
            )
        return window_start, window_end
