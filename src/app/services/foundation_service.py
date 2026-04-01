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
    FoundationPartialFailure,
    FoundationPerformanceSummary,
    FoundationPortfolioCatalogItem,
    FoundationPortfolioCatalogResponse,
    FoundationPortfolioIdentity,
    FoundationPortfolioSummary,
    FoundationRebalanceSummary,
    FoundationReportingReadiness,
    FoundationWorkflowLaunchCue,
    FoundationWorkspaceReadiness,
    FoundationWorkspaceResponse,
)
from app.precision_policy import quantize_money, quantize_performance


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
        status_code, payload = await self._lotus_core_query_client.get_portfolio_lookups(
            correlation_id=correlation_id
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core portfolio catalog unavailable: {payload}",
            )

        items_payload = payload.get("items", [])
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
        as_of_date = datetime.now(UTC).date().isoformat()
        pas_status, pas_payload = await self._lotus_core_query_client.get_core_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
            consumer_system="lotus-gateway",
            correlation_id=correlation_id,
        )
        if pas_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core foundation snapshot unavailable: {pas_payload}",
            )

        portfolio, summary, allocations, as_of_date = self._parse_core_snapshot(
            fallback_portfolio_id=portfolio_id,
            payload=pas_payload,
            fallback_as_of_date=as_of_date,
        )

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
        gathered = await asyncio.gather(
            performance_task,
            rebalance_task,
            reporting_task,
            return_exceptions=True,
        )

        warnings: list[str] = []
        partial_failures: list[FoundationPartialFailure] = []

        performance = self._parse_performance_result(
            result=cast(object, gathered[0]),
            warnings=warnings,
            partial_failures=partial_failures,
        )
        rebalance = self._parse_rebalance_result(
            result=cast(object, gathered[1]),
            warnings=warnings,
            partial_failures=partial_failures,
        )
        reporting = self._parse_reporting_result(
            result=cast(object, gathered[2]),
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
            summary=summary,
            allocations=allocations,
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
        display_name = str(
            item.get("portfolio_name")
            or item.get("name")
            or item.get("label")
            or item.get("display_name")
            or portfolio_id
        )
        return FoundationPortfolioCatalogItem(
            portfolio_id=portfolio_id,
            display_name=display_name,
            base_currency=str(item.get("base_currency", "USD")),
            client_id=self._optional_str(item.get("cif_id", item.get("client_id"))),
            booking_center_code=self._optional_str(
                item.get("booking_center", item.get("booking_center_code"))
            ),
        )

    def _parse_core_snapshot(
        self,
        fallback_portfolio_id: str,
        payload: dict[str, Any],
        fallback_as_of_date: str,
    ) -> tuple[
        FoundationPortfolioIdentity,
        FoundationPortfolioSummary,
        list[FoundationAllocationBucket],
        str,
    ]:
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core foundation snapshot payload structure.",
            )

        portfolio_payload = payload.get("portfolio", {})
        sections_payload = payload.get("sections", {})
        metadata_payload = payload.get("metadata", {})
        if not isinstance(portfolio_payload, dict) or not isinstance(sections_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core foundation snapshot payload structure.",
            )

        baseline_rows = sections_payload.get("positions_baseline", [])
        if not isinstance(baseline_rows, list):
            baseline_rows = []
        totals_payload = sections_payload.get("portfolio_totals", {})
        if not isinstance(totals_payload, dict):
            totals_payload = {}
        enrichment_rows = sections_payload.get("instrument_enrichment", [])
        if not isinstance(enrichment_rows, list):
            enrichment_rows = []

        market_value_base = float(
            quantize_money(totals_payload.get("baseline_total_market_value_base", 0.0))
        )
        total_cash_base = float(quantize_money(totals_payload.get("baseline_total_cash_base", 0.0)))
        cash_weight_pct = 0.0
        if market_value_base > 0:
            cash_weight_pct = float(
                quantize_performance((total_cash_base / market_value_base) * 100.0)
            )

        enrichment_by_security_id: dict[str, dict[str, Any]] = {}
        for row in enrichment_rows:
            if not isinstance(row, dict):
                continue
            security_id = self._optional_str(row.get("security_id"))
            if security_id is not None:
                enrichment_by_security_id[security_id] = row

        allocations_by_asset_class: dict[str, FoundationAllocationBucket] = {}
        position_count = 0
        for row in baseline_rows:
            if not isinstance(row, dict):
                continue
            position_count += 1
            security_id = self._optional_str(row.get("security_id"))
            enrichment = enrichment_by_security_id.get(security_id or "", {})
            asset_class = str(
                enrichment.get("asset_class")
                or enrichment.get("asset_class_name")
                or row.get("asset_class")
                or "Unclassified"
            )
            bucket = allocations_by_asset_class.get(asset_class)
            if bucket is None:
                bucket = FoundationAllocationBucket(
                    asset_class=asset_class,
                    position_count=0,
                    market_value_base=0.0,
                    weight_pct=None,
                )
                allocations_by_asset_class[asset_class] = bucket
            bucket.position_count += 1
            market_value = self._extract_market_value(row)
            if market_value is not None:
                current_market_value = bucket.market_value_base or 0.0
                bucket.market_value_base = float(
                    quantize_money(current_market_value + market_value)
                )

        allocations = sorted(allocations_by_asset_class.values(), key=lambda item: item.asset_class)
        for bucket in allocations:
            if bucket.market_value_base is not None and market_value_base > 0:
                bucket.weight_pct = float(
                    quantize_performance((bucket.market_value_base / market_value_base) * 100.0)
                )

        portfolio_id = str(portfolio_payload.get("portfolio_id", fallback_portfolio_id))
        display_name = str(
            portfolio_payload.get("portfolio_name") or portfolio_payload.get("name") or portfolio_id
        )
        portfolio = FoundationPortfolioIdentity(
            portfolio_id=portfolio_id,
            display_name=display_name,
            client_id=self._optional_str(
                portfolio_payload.get("cif_id", portfolio_payload.get("client_id"))
            ),
            base_currency=str(portfolio_payload.get("base_currency", "USD")),
            booking_center_code=self._optional_str(
                portfolio_payload.get(
                    "booking_center",
                    portfolio_payload.get("booking_center_code"),
                )
            ),
        )
        summary = FoundationPortfolioSummary(
            market_value_base=market_value_base,
            total_cash_base=total_cash_base,
            cash_weight_pct=cash_weight_pct,
            position_count=position_count,
        )
        as_of_date = str(
            payload.get("as_of_date")
            or metadata_payload.get("as_of_date")
            or metadata_payload.get("business_date")
            or fallback_as_of_date
        )
        return portfolio, summary, allocations, as_of_date

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

        results_by_period = payload.get("resultsByPeriod", {})
        if not isinstance(results_by_period, dict):
            warnings.append("FOUNDATION_PERFORMANCE_INVALID")
            return None

        period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period), None)
        if period_key is None:
            return None

        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        return FoundationPerformanceSummary(
            period=period_key,
            return_pct=period_payload.get("net_cumulative_return"),
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
