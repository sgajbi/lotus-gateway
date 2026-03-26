import asyncio
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.foundation import (
    FoundationAllocationBucket,
    FoundationCashflowOutlook,
    FoundationCashflowPoint,
    FoundationPartialFailure,
    FoundationPerformanceSummary,
    FoundationPortfolioCatalogItem,
    FoundationPortfolioCatalogResponse,
    FoundationPortfolioIdentity,
    FoundationPortfolioProfile,
    FoundationPortfolioSummary,
    FoundationPositionView,
    FoundationRebalanceSummary,
    FoundationReportingReadiness,
    FoundationTopPosition,
    FoundationTransactionView,
    FoundationWorkflowLaunchCue,
    FoundationWorkspaceReadiness,
    FoundationWorkspaceResponse,
)
from app.precision_policy import quantize_money, quantize_performance, quantize_quantity


class FoundationService:
    def __init__(
        self,
        lotus_core_query_client: LotusCoreQueryClient,
        analytics_client: LotusAnalyticsClient,
        dpm_client: DpmClient,
        reporting_client: ReportingClient,
    ):
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._dpm_client = dpm_client
        self._reporting_client = reporting_client

    async def get_portfolio_catalog(
        self,
        correlation_id: str,
    ) -> FoundationPortfolioCatalogResponse:
        status_code, payload = await self._lotus_core_query_client.list_portfolios(
            correlation_id=correlation_id
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core portfolio catalog unavailable: {payload}",
            )

        items_payload = payload.get("portfolios", payload.get("items", []))
        if not isinstance(items_payload, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core portfolio catalog payload structure.",
            )

        items = [self._parse_catalog_item(item) for item in items_payload if isinstance(item, dict)]
        items.sort(key=lambda item: item.portfolio_id)

        return FoundationPortfolioCatalogResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            items=items,
        )

    async def get_portfolio_workspace(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> FoundationWorkspaceResponse:
        requested_as_of_date = datetime.now(UTC).date().isoformat()
        (
            portfolio_result,
            positions_result,
            snapshot_result,
            transactions_result,
            cashflow_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_portfolio_positions(
                portfolio_id=portfolio_id,
                as_of_date=requested_as_of_date,
                include_projected=False,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_core_snapshot(
                portfolio_id=portfolio_id,
                as_of_date=requested_as_of_date,
                sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_portfolio_transactions(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                limit=8,
                sort_by="transaction_date",
                sort_order="desc",
                as_of_date=requested_as_of_date,
                include_projected=False,
            ),
            self._lotus_core_query_client.get_cashflow_projection(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
                horizon_days=10,
                as_of_date=requested_as_of_date,
                include_projected=True,
            ),
        )

        portfolio_payload = self._require_core_payload(
            result=portfolio_result,
            unavailable_detail_prefix="lotus-core portfolio record unavailable",
        )
        positions_payload = self._require_core_payload(
            result=positions_result,
            unavailable_detail_prefix="lotus-core positions unavailable",
        )
        snapshot_payload = self._require_core_payload(
            result=snapshot_result,
            unavailable_detail_prefix="lotus-core core snapshot unavailable",
        )

        portfolio, profile = self._parse_portfolio_record(portfolio_payload)
        positions = self._parse_positions_payload(positions_payload)
        as_of_date, summary = self._parse_snapshot_summary(
            payload=snapshot_payload,
            fallback_as_of_date=requested_as_of_date,
            positions=positions,
        )
        allocations = self._build_allocation_buckets(
            rows=positions,
            total_market_value=summary.market_value_base,
        )
        top_positions = self._build_top_positions(rows=positions)

        performance_task = self._analytics_client.get_stateful_twr(
            portfolio_id=portfolio_id,
            report_end_date=as_of_date,
            period="YTD",
            correlation_id=correlation_id,
        )
        rebalance_task = self._dpm_client.list_runs(
            params={"portfolio_id": portfolio_id, "limit": 1},
            correlation_id=correlation_id,
        )
        reporting_task = self._reporting_client.get_portfolio_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
        optional_results = await asyncio.gather(
            performance_task,
            rebalance_task,
            reporting_task,
            return_exceptions=True,
        )

        warnings: list[str] = []
        partial_failures: list[FoundationPartialFailure] = []

        recent_transactions = self._parse_transactions_result(
            result=transactions_result,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        cashflow_outlook = self._parse_cashflow_result(
            result=cashflow_result,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        performance = self._parse_performance_result(
            result=cast(object, optional_results[0]),
            warnings=warnings,
            partial_failures=partial_failures,
        )
        rebalance = self._parse_rebalance_result(
            result=cast(object, optional_results[1]),
            warnings=warnings,
            partial_failures=partial_failures,
        )
        reporting = self._parse_reporting_result(
            result=cast(object, optional_results[2]),
            warnings=warnings,
            partial_failures=partial_failures,
        )

        readiness = FoundationWorkspaceReadiness(
            has_positions=summary.position_count > 0,
            reporting=reporting,
        )

        return FoundationWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=as_of_date,
            portfolio=portfolio,
            profile=profile,
            summary=summary,
            allocations=allocations,
            top_positions=top_positions,
            positions=positions,
            recent_transactions=recent_transactions,
            cashflow_outlook=cashflow_outlook,
            performance=performance,
            rebalance=rebalance,
            readiness=readiness,
            workflow_cues=self._build_workflow_cues(portfolio_id=portfolio_id),
            warnings=warnings,
            partial_failures=partial_failures,
        )

    def _parse_catalog_item(self, item: dict[str, Any]) -> FoundationPortfolioCatalogItem:
        portfolio_id = str(item.get("portfolio_id", item.get("id", ""))).strip()
        if not portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core portfolio catalog item without portfolio_id.",
            )
        return FoundationPortfolioCatalogItem(
            portfolio_id=portfolio_id,
            display_name=portfolio_id,
            base_currency=str(item.get("base_currency", "USD")),
            client_id=self._optional_str(item.get("client_id", item.get("cif_id"))),
            booking_center_code=self._optional_str(
                item.get("booking_center_code", item.get("booking_center"))
            ),
        )

    def _parse_portfolio_record(
        self,
        payload: dict[str, Any],
    ) -> tuple[FoundationPortfolioIdentity, FoundationPortfolioProfile]:
        portfolio_id = str(payload.get("portfolio_id", "")).strip()
        if not portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core portfolio record without portfolio_id.",
            )
        portfolio = FoundationPortfolioIdentity(
            portfolio_id=portfolio_id,
            display_name=portfolio_id,
            client_id=self._optional_str(payload.get("client_id")),
            base_currency=str(payload.get("base_currency", "USD")),
            booking_center_code=self._optional_str(payload.get("booking_center_code")),
        )
        profile = FoundationPortfolioProfile(
            status=self._optional_str(payload.get("status")),
            portfolio_type=self._optional_str(payload.get("portfolio_type")),
            risk_exposure=self._optional_str(payload.get("risk_exposure")),
            investment_time_horizon=self._optional_str(payload.get("investment_time_horizon")),
            objective=self._optional_str(payload.get("objective")),
            is_leverage_allowed=(
                bool(payload.get("is_leverage_allowed"))
                if payload.get("is_leverage_allowed") is not None
                else None
            ),
            advisor_id=self._optional_str(payload.get("advisor_id")),
            open_date=self._optional_str(payload.get("open_date")),
            close_date=self._optional_str(payload.get("close_date")),
        )
        return portfolio, profile

    def _parse_snapshot_summary(
        self,
        payload: dict[str, Any],
        fallback_as_of_date: str,
        positions: list[FoundationPositionView],
    ) -> tuple[str, FoundationPortfolioSummary]:
        sections_payload = payload.get("sections", {})
        if not isinstance(sections_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core core snapshot payload structure.",
            )
        portfolio_totals = sections_payload.get("portfolio_totals", {})
        if not isinstance(portfolio_totals, dict):
            portfolio_totals = {}

        market_value_base = self._optional_money(
            portfolio_totals.get("baseline_total_market_value_base")
        )
        if market_value_base is None:
            market_value_base = float(
                quantize_money(sum(position.market_value_base or 0.0 for position in positions))
            )

        total_cash_base = float(
            quantize_money(
                sum(
                    position.market_value_base or 0.0
                    for position in positions
                    if (position.asset_class or "").lower() == "cash"
                )
            )
        )
        cash_weight_pct = 0.0
        if market_value_base > 0:
            cash_weight_pct = float(
                quantize_performance((total_cash_base / market_value_base) * 100.0)
            )

        summary = FoundationPortfolioSummary(
            market_value_base=market_value_base,
            total_cash_base=total_cash_base,
            cash_weight_pct=cash_weight_pct,
            position_count=len(positions),
        )
        return str(payload.get("as_of_date", fallback_as_of_date)), summary

    def _parse_positions_payload(
        self,
        payload: dict[str, Any],
    ) -> list[FoundationPositionView]:
        positions_payload = payload.get("positions", [])
        if not isinstance(positions_payload, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core positions payload structure.",
            )

        rows: list[FoundationPositionView] = []
        for item in positions_payload:
            if not isinstance(item, dict):
                continue
            weight_pct = None
            if item.get("weight") is not None:
                try:
                    weight_pct = float(quantize_performance(float(item["weight"]) * 100.0))
                except (TypeError, ValueError):
                    weight_pct = None
            rows.append(
                FoundationPositionView(
                    security_id=str(item.get("security_id", "UNKNOWN")),
                    instrument_name=str(
                        item.get("instrument_name", item.get("security_id", "UNKNOWN"))
                    ),
                    asset_class=self._optional_str(item.get("asset_class")),
                    isin=self._optional_str(item.get("isin")),
                    currency=self._optional_str(item.get("currency")),
                    sector=self._optional_str(item.get("sector")),
                    country_of_risk=self._optional_str(item.get("country_of_risk")),
                    held_since_date=self._optional_str(item.get("held_since_date")),
                    quantity=float(quantize_quantity(item.get("quantity", 0.0))),
                    cost_basis_base=self._optional_money(item.get("cost_basis")),
                    market_value_base=self._extract_market_value(item),
                    weight_pct=weight_pct,
                    reprocessing_status=self._optional_str(item.get("reprocessing_status")),
                )
            )
        rows.sort(
            key=lambda row: (
                row.market_value_base is None,
                -(row.market_value_base or 0.0),
                row.security_id,
            )
        )
        return rows

    def _build_allocation_buckets(
        self,
        rows: list[FoundationPositionView],
        total_market_value: float,
    ) -> list[FoundationAllocationBucket]:
        grouped: dict[str, list[FoundationPositionView]] = {}
        for row in rows:
            grouped.setdefault(row.asset_class or "Unclassified", []).append(row)

        allocations: list[FoundationAllocationBucket] = []
        for asset_class, bucket_rows in grouped.items():
            market_value = float(
                quantize_money(sum(row.market_value_base or 0.0 for row in bucket_rows))
            )
            weight_pct = None
            if total_market_value > 0:
                weight_pct = float(
                    quantize_performance((market_value / total_market_value) * 100.0)
                )
            allocations.append(
                FoundationAllocationBucket(
                    asset_class=asset_class,
                    position_count=len(bucket_rows),
                    market_value_base=market_value,
                    weight_pct=weight_pct,
                )
            )
        allocations.sort(key=lambda row: row.asset_class)
        return allocations

    def _build_top_positions(
        self,
        rows: list[FoundationPositionView],
    ) -> list[FoundationTopPosition]:
        return [
            FoundationTopPosition(
                security_id=row.security_id,
                instrument_name=row.instrument_name,
                asset_class=row.asset_class,
                isin=row.isin,
                currency=row.currency,
                quantity=row.quantity,
                cost_basis_base=row.cost_basis_base,
                market_value_base=row.market_value_base,
                weight_pct=row.weight_pct,
            )
            for row in rows[:5]
        ]

    def _parse_performance_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationPerformanceSummary | None:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-performance",
            unavailable_warning="FOUNDATION_PERFORMANCE_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return None

        results_by_period = payload.get("results_by_period", payload.get("resultsByPeriod", {}))
        if not isinstance(results_by_period, dict):
            warnings.append("FOUNDATION_PERFORMANCE_INVALID")
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
            period_return_payload = {}
        return FoundationPerformanceSummary(
            period=period_key,
            return_pct=period_return_payload.get("base"),
        )

    def _parse_rebalance_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationRebalanceSummary | None:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-manage",
            unavailable_warning="FOUNDATION_REBALANCE_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return None

        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            return FoundationRebalanceSummary(status="NOT_AVAILABLE")

        latest = items[0]
        if not isinstance(latest, dict):
            return FoundationRebalanceSummary(status="NOT_AVAILABLE")

        return FoundationRebalanceSummary(
            status=str(latest.get("status", "UNKNOWN")),
            last_run_at_utc=self._optional_str(latest.get("created_at")),
            last_rebalance_run_id=self._optional_str(latest.get("rebalance_run_id")),
        )

    def _parse_reporting_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationReportingReadiness:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-report",
            unavailable_warning="FOUNDATION_REPORTING_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return FoundationReportingReadiness(status="UNAVAILABLE")

        rows = payload.get("rows", [])
        if not isinstance(rows, list):
            rows = []
        generated_at = self._optional_str(payload.get("generatedAt"))
        status_value = "READY" if rows else "EMPTY"
        return FoundationReportingReadiness(
            status=status_value,
            generated_at_utc=generated_at,
            row_count=len(rows),
        )

    def _parse_transactions_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> list[FoundationTransactionView]:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-core",
            unavailable_warning="FOUNDATION_TRANSACTIONS_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return []

        rows = payload.get("transactions", [])
        if not isinstance(rows, list):
            warnings.append("FOUNDATION_TRANSACTIONS_INVALID")
            return []

        return [
            FoundationTransactionView(
                transaction_id=str(item.get("transaction_id", "")),
                transaction_date=str(item.get("transaction_date", "")),
                transaction_type=str(item.get("transaction_type", "")),
                security_id=str(item.get("security_id", "")),
                instrument_id=str(item.get("instrument_id", "")),
                quantity=float(quantize_quantity(item.get("quantity", 0.0))),
                price=self._optional_money(item.get("price")),
                gross_amount=self._optional_money(item.get("gross_transaction_amount")),
                currency=self._optional_str(item.get("currency")),
                net_cost_base=self._optional_money(item.get("net_cost")),
                realized_gain_loss_base=self._optional_money(item.get("realized_gain_loss")),
                settlement_status=self._optional_str(item.get("settlement_status")),
            )
            for item in rows
            if isinstance(item, dict)
        ]

    def _parse_cashflow_result(
        self,
        result: object,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> FoundationCashflowOutlook | None:
        _, payload = self._unpack_optional_upstream(
            result=result,
            source_service="lotus-core",
            unavailable_warning="FOUNDATION_CASHFLOW_UNAVAILABLE",
            warnings=warnings,
            partial_failures=partial_failures,
        )
        if payload is None:
            return None

        points = payload.get("points", [])
        if not isinstance(points, list):
            warnings.append("FOUNDATION_CASHFLOW_INVALID")
            return None

        return FoundationCashflowOutlook(
            as_of_date=str(payload.get("as_of_date", "")),
            range_end_date=str(payload.get("range_end_date", "")),
            total_net_cashflow_base=float(quantize_money(payload.get("total_net_cashflow", 0.0))),
            projection_days=int(payload.get("projection_days", 0)),
            include_projected=bool(payload.get("include_projected", False)),
            notes=self._optional_str(payload.get("notes")),
            upcoming_points=[
                FoundationCashflowPoint(
                    projection_date=str(item.get("projection_date", "")),
                    net_cashflow_base=float(quantize_money(item.get("net_cashflow", 0.0))),
                    projected_cumulative_cashflow_base=float(
                        quantize_money(item.get("projected_cumulative_cashflow", 0.0))
                    ),
                )
                for item in points[:5]
                if isinstance(item, dict)
            ],
        )

    def _unpack_optional_upstream(
        self,
        result: object,
        source_service: str,
        unavailable_warning: str,
        warnings: list[str],
        partial_failures: list[FoundationPartialFailure],
    ) -> tuple[int | None, dict[str, Any] | None]:
        if isinstance(result, Exception):
            partial_failures.append(
                FoundationPartialFailure(
                    source_service=source_service,
                    error_code="UPSTREAM_EXCEPTION",
                    detail=str(result),
                )
            )
            warnings.append(unavailable_warning)
            return None, None

        if not isinstance(result, tuple) or len(result) != 2:
            partial_failures.append(
                FoundationPartialFailure(
                    source_service=source_service,
                    error_code="INVALID_UPSTREAM_RESPONSE",
                    detail=f"unexpected result type: {type(result)}",
                )
            )
            warnings.append(unavailable_warning)
            return None, None

        status_code, payload = result
        if not isinstance(payload, dict):
            partial_failures.append(
                FoundationPartialFailure(
                    source_service=source_service,
                    error_code="INVALID_UPSTREAM_PAYLOAD",
                    detail=f"unexpected payload type: {type(payload)}",
                )
            )
            warnings.append(unavailable_warning)
            return status_code, None

        if status_code >= status.HTTP_400_BAD_REQUEST:
            partial_failures.append(
                FoundationPartialFailure(
                    source_service=source_service,
                    error_code=f"HTTP_{status_code}",
                    detail=str(payload.get("detail", payload)),
                )
            )
            warnings.append(unavailable_warning)
            return status_code, None

        return status_code, payload

    def _require_core_payload(
        self,
        result: object,
        unavailable_detail_prefix: str,
    ) -> dict[str, Any]:
        if not isinstance(result, tuple) or len(result) != 2:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{unavailable_detail_prefix}: unexpected result type {type(result)}",
            )
        status_code, payload = result
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{unavailable_detail_prefix}: invalid payload type {type(payload)}",
            )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{unavailable_detail_prefix}: {payload}",
            )
        return payload

    def _extract_market_value(self, item: dict[str, Any]) -> float | None:
        valuation = item.get("valuation")
        if isinstance(valuation, dict):
            for key in ("market_value_base", "market_value", "current_value_base", "current_value"):
                value = valuation.get(key)
                if value is None:
                    continue
                try:
                    return float(quantize_money(value))
                except (TypeError, ValueError):
                    continue
        for key in (
            "market_value_base",
            "market_value",
            "current_value_base",
            "current_value",
            "valuation_base",
            "value_base",
        ):
            value = item.get(key)
            if value is None:
                continue
            try:
                return float(quantize_money(value))
            except (TypeError, ValueError):
                continue
        return None

    def _build_workflow_cues(self, portfolio_id: str) -> list[FoundationWorkflowLaunchCue]:
        return [
            FoundationWorkflowLaunchCue(
                key="performance",
                label="Open Performance",
                href=f"/app/performance?portfolioId={portfolio_id}",
            ),
            FoundationWorkflowLaunchCue(
                key="risk",
                label="Open Risk",
                href=f"/app/risk?portfolioId={portfolio_id}",
            ),
            FoundationWorkflowLaunchCue(
                key="proposal",
                label="Open Proposal",
                href=f"/app/proposal?portfolioId={portfolio_id}",
            ),
        ]

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _optional_money(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(quantize_money(value))
        except (TypeError, ValueError):
            return None
