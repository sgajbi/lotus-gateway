import asyncio
from collections.abc import Awaitable
from datetime import UTC, date, datetime
from typing import Any, cast

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.config import settings
from app.contracts.workbench import (
    WorkbenchAnalyticsBucket,
    WorkbenchAnalyticsResponse,
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPolicyFeedback,
    WorkbenchPortfolio360Response,
    WorkbenchPortfolioSummary,
    WorkbenchPositionView,
    WorkbenchProjectedPositionView,
    WorkbenchProjectedSummary,
    WorkbenchRebalanceSnapshot,
    WorkbenchSandboxStateResponse,
    WorkbenchTopChange,
)
from app.precision_policy import (
    quantize_money,
    quantize_performance,
    quantize_quantity,
)


class WorkbenchService:
    def __init__(
        self,
        lotus_core_query_client: LotusCoreQueryClient,
        analytics_client: LotusAnalyticsClient,
        dpm_client: DpmClient,
    ):
        self._lotus_core_query_client = lotus_core_query_client
        self._analytics_client = analytics_client
        self._dpm_client = dpm_client

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,
        include_rebalance_snapshot: bool = True,
    ) -> WorkbenchOverviewResponse:
        as_of_date = date.today().isoformat()
        (
            portfolio_result,
            snapshot_result,
        ) = await asyncio.gather(
            self._lotus_core_query_client.get_portfolio(
                portfolio_id=portfolio_id,
                correlation_id=correlation_id,
            ),
            self._lotus_core_query_client.get_core_snapshot(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            ),
        )
        portfolio_status, portfolio_payload = portfolio_result
        snapshot_status, snapshot_payload = snapshot_result
        self._raise_for_lotus_core_error(portfolio_status, portfolio_payload)
        self._raise_for_lotus_core_error(snapshot_status, snapshot_payload)

        portfolio, overview, as_of_date = self._parse_lotus_core_snapshot(
            fallback_portfolio_id=portfolio_id,
            portfolio_payload=portfolio_payload,
            snapshot_payload=snapshot_payload,
            fallback_as_of_date=as_of_date,
        )
        partial_failures: list[WorkbenchPartialFailure] = []
        warnings: list[str] = []
        performance_snapshot = None
        rebalance_snapshot = None

        if include_performance_snapshot or include_rebalance_snapshot:
            performance_task: Awaitable[tuple[int, dict[str, Any]]]
            if include_performance_snapshot:
                performance_end_date = await self._resolve_performance_snapshot_end_date(
                    portfolio_id=portfolio_id,
                    as_of_date=as_of_date,
                    correlation_id=correlation_id,
                )
                performance_task = self._analytics_client.get_twr_analytics(
                    portfolio_id=portfolio_id,
                    report_end_date=performance_end_date,
                    report_start_date=None,
                    period="YTD",
                    metric_basis="NET",
                    benchmark_id=None,
                    correlation_id=correlation_id,
                )
            else:
                performance_task = self._empty_async_result()

            dpm_task = (
                self._dpm_client.list_runs(
                    params={"portfolio_id": portfolio_id, "limit": 1},
                    correlation_id=correlation_id,
                )
                if include_rebalance_snapshot
                else self._empty_async_result()
            )
            gathered = await asyncio.gather(performance_task, dpm_task, return_exceptions=True)
            if include_performance_snapshot:
                performance_snapshot = self._parse_performance_snapshot(
                    result=cast(object, gathered[0]),
                    partial_failures=partial_failures,
                    warnings=warnings,
                )
            if include_rebalance_snapshot:
                rebalance_snapshot = self._parse_dpm_snapshot(
                    result=cast(object, gathered[1]),
                    partial_failures=partial_failures,
                    warnings=warnings,
                )

        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=as_of_date,
            portfolio=portfolio,
            overview=overview,
            performance_snapshot=performance_snapshot,
            rebalance_snapshot=rebalance_snapshot,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    async def _resolve_performance_snapshot_end_date(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> str:
        (
            status_code,
            payload,
        ) = await self._lotus_core_query_client.get_portfolio_analytics_reference(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            consumer_system="lotus-gateway",
            correlation_id=correlation_id,
        )
        if status_code >= status.HTTP_400_BAD_REQUEST or not isinstance(payload, dict):
            return as_of_date

        performance_end_date = payload.get("performance_end_date")
        if not isinstance(performance_end_date, str) or not performance_end_date.strip():
            return as_of_date
        return performance_end_date

    async def get_portfolio_360(
        self,
        portfolio_id: str,
        correlation_id: str,
        session_id: str | None = None,
    ) -> WorkbenchPortfolio360Response:
        overview = await self.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )

        (
            passthrough_status,
            passthrough_payload,
        ) = await self._lotus_core_query_client.get_core_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            sections=["positions_baseline", "portfolio_totals", "instrument_enrichment"],
            consumer_system="lotus-gateway",
            correlation_id=correlation_id,
        )
        self._raise_for_lotus_core_error(passthrough_status, passthrough_payload)
        current_positions = self._extract_current_positions(passthrough_payload)

        projected_positions: list[WorkbenchProjectedPositionView] = []
        projected_summary: WorkbenchProjectedSummary | None = None
        if session_id:
            projected_positions, projected_summary = await self._load_projected_state(
                session_id=session_id,
                correlation_id=correlation_id,
            )

        return WorkbenchPortfolio360Response(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=overview.as_of_date,
            portfolio=overview.portfolio,
            overview=overview.overview,
            performance_snapshot=overview.performance_snapshot,
            rebalance_snapshot=overview.rebalance_snapshot,
            current_positions=current_positions,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            active_session_id=session_id,
            warnings=overview.warnings,
            partial_failures=overview.partial_failures,
        )

    async def create_sandbox_session(
        self,
        portfolio_id: str,
        correlation_id: str,
        created_by: str | None,
        ttl_hours: int,
    ) -> WorkbenchSandboxStateResponse:
        status_code, payload = await self._lotus_core_query_client.create_simulation_session(
            portfolio_id=portfolio_id,
            created_by=created_by,
            ttl_hours=ttl_hours,
            correlation_id=correlation_id,
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core simulation session create failed: {payload}",
            )

        session_payload = payload.get("session", {})
        session_id = str(session_payload.get("session_id", ""))
        session_version = int(session_payload.get("version", 1))
        projected_positions, projected_summary = await self._load_projected_state(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        return WorkbenchSandboxStateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            policy_feedback=None,
            warnings=[],
            partial_failures=[],
        )

    async def apply_sandbox_changes(
        self,
        portfolio_id: str,
        session_id: str,
        correlation_id: str,
        changes: list[dict[str, Any]],
        evaluate_policy: bool,
    ) -> WorkbenchSandboxStateResponse:
        status_code, payload = await self._lotus_core_query_client.add_simulation_changes(
            session_id=session_id,
            changes=changes,
            correlation_id=correlation_id,
        )
        if status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core simulation change apply failed: {payload}",
            )

        session_version = int(payload.get("version", 1))
        projected_positions, projected_summary = await self._load_projected_state(
            session_id=session_id,
            correlation_id=correlation_id,
        )

        warnings: list[str] = []
        partial_failures: list[WorkbenchPartialFailure] = []
        policy_feedback: WorkbenchPolicyFeedback | None = None
        if evaluate_policy:
            policy_feedback = await self._evaluate_policy_feedback(
                portfolio_id=portfolio_id,
                session_id=session_id,
                session_version=session_version,
                projected_positions=projected_positions,
                correlation_id=correlation_id,
                warnings=warnings,
                partial_failures=partial_failures,
            )

        return WorkbenchSandboxStateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            policy_feedback=policy_feedback,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def get_workbench_analytics(
        self,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        group_by: str,
        benchmark_code: str,
        session_id: str | None,
    ) -> WorkbenchAnalyticsResponse:
        portfolio_360 = await self.get_portfolio_360(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            session_id=session_id,
        )
        analytics_payload = {
            "portfolioId": portfolio_id,
            "asOfDate": portfolio_360.as_of_date,
            "period": period,
            "groupBy": group_by,
            "benchmarkCode": benchmark_code,
            "portfolioReturnPct": (
                portfolio_360.performance_snapshot.return_pct
                if portfolio_360.performance_snapshot is not None
                else None
            ),
            "benchmarkReturnPct": (
                portfolio_360.performance_snapshot.benchmark_return_pct
                if portfolio_360.performance_snapshot is not None
                else None
            ),
            "currentPositions": [
                {
                    "securityId": row.security_id,
                    "instrumentName": row.instrument_name,
                    "assetClass": row.asset_class,
                    "quantity": row.quantity,
                }
                for row in portfolio_360.current_positions
            ],
            "projectedPositions": [
                {
                    "securityId": row.security_id,
                    "instrumentName": row.instrument_name,
                    "assetClass": row.asset_class,
                    "baselineQuantity": row.baseline_quantity,
                    "proposedQuantity": row.proposed_quantity,
                    "deltaQuantity": row.delta_quantity,
                }
                for row in portfolio_360.projected_positions
            ],
        }
        analytics_status, analytics_response = await self._analytics_client.get_workbench_analytics(
            payload=analytics_payload,
            correlation_id=correlation_id,
        )
        if analytics_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-performance workbench analytics unavailable: {analytics_response}",
            )

        try:
            allocation_buckets = [
                WorkbenchAnalyticsBucket(
                    bucket_key=str(item.get("bucketKey", "")),
                    bucket_label=str(item.get("bucketLabel", "")),
                    current_quantity=float(quantize_quantity(item.get("currentQuantity", 0.0))),
                    proposed_quantity=float(quantize_quantity(item.get("proposedQuantity", 0.0))),
                    delta_quantity=float(quantize_quantity(item.get("deltaQuantity", 0.0))),
                    current_weight_pct=float(
                        quantize_performance(item.get("currentWeightPct", 0.0))
                    ),
                    proposed_weight_pct=float(
                        quantize_performance(item.get("proposedWeightPct", 0.0))
                    ),
                )
                for item in analytics_response.get("allocationBuckets", [])
                if isinstance(item, dict)
            ]
            top_changes = [
                WorkbenchTopChange(
                    security_id=str(item.get("securityId", "")),
                    instrument_name=str(item.get("instrumentName", "")),
                    delta_quantity=float(quantize_quantity(item.get("deltaQuantity", 0.0))),
                    direction=str(item.get("direction", "UNKNOWN")),
                )
                for item in analytics_response.get("topChanges", [])
                if isinstance(item, dict)
            ]
            warnings = list(portfolio_360.warnings)
            if "RISK_BFF_PENDING" not in warnings:
                warnings.append("RISK_BFF_PENDING")
            partial_failures = list(portfolio_360.partial_failures)
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="risk",
                    error_code="RISK_BFF_NOT_IMPLEMENTED",
                    detail=(
                        "Legacy workbench risk proxy was removed. Stateful concentration risk "
                        "will be restored through the RFC-0022 Gateway Risk BFF."
                    ),
                )
            )
            portfolio_360 = portfolio_360.model_copy(
                update={"warnings": warnings, "partial_failures": partial_failures}
            )
            portfolio_return = analytics_response.get("portfolioReturnPct")
            benchmark_return = analytics_response.get("benchmarkReturnPct")
            active_return = analytics_response.get("activeReturnPct")
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid lotus-performance workbench analytics payload: {exc}",
            ) from exc

        return WorkbenchAnalyticsResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            period=period,
            group_by=group_by,
            benchmark_code=benchmark_code,
            portfolio_return_pct=(
                float(quantize_performance(portfolio_return))
                if portfolio_return is not None
                else None
            ),
            benchmark_return_pct=(
                float(quantize_performance(benchmark_return))
                if benchmark_return is not None
                else None
            ),
            active_return_pct=(
                float(quantize_performance(active_return)) if active_return is not None else None
            ),
            allocation_buckets=allocation_buckets,
            top_changes=top_changes,
            risk_proxy=None,
            warnings=portfolio_360.warnings,
            partial_failures=portfolio_360.partial_failures,
        )

    def _raise_for_lotus_core_error(self, upstream_status: int, payload: dict[str, Any]) -> None:
        if upstream_status < status.HTTP_400_BAD_REQUEST:
            return
        detail = str(payload.get("detail", payload))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"lotus-core core snapshot unavailable: {detail}",
        )

    async def _load_projected_state(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[list[WorkbenchProjectedPositionView], WorkbenchProjectedSummary]:
        (
            positions_status,
            positions_payload,
        ) = await self._lotus_core_query_client.get_projected_positions(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if positions_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core projected positions unavailable: {positions_payload}",
            )

        summary_status, summary_payload = await self._lotus_core_query_client.get_projected_summary(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if summary_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"lotus-core projected summary unavailable: {summary_payload}",
            )

        rows_payload = positions_payload.get("positions", [])
        rows: list[WorkbenchProjectedPositionView] = []
        if isinstance(rows_payload, list):
            for row in rows_payload:
                if not isinstance(row, dict):
                    continue
                rows.append(
                    WorkbenchProjectedPositionView(
                        security_id=str(row.get("security_id", "")),
                        instrument_name=str(
                            row.get("instrument_name", row.get("security_id", "UNKNOWN"))
                        ),
                        asset_class=(
                            str(row["asset_class"]) if row.get("asset_class") is not None else None
                        ),
                        baseline_quantity=float(
                            quantize_quantity(row.get("baseline_quantity", 0.0))
                        ),
                        proposed_quantity=float(
                            quantize_quantity(row.get("proposed_quantity", 0.0))
                        ),
                        delta_quantity=float(quantize_quantity(row.get("delta_quantity", 0.0))),
                    )
                )

        summary = WorkbenchProjectedSummary(
            total_baseline_positions=int(summary_payload.get("total_baseline_positions", 0)),
            total_proposed_positions=int(summary_payload.get("total_proposed_positions", 0)),
            net_delta_quantity=float(
                quantize_quantity(summary_payload.get("net_delta_quantity", 0.0))
            ),
        )
        return rows, summary

    def _extract_current_positions(
        self, snapshot_payload: dict[str, Any]
    ) -> list[WorkbenchPositionView]:
        sections_payload = snapshot_payload.get("sections", {})
        if not isinstance(sections_payload, dict):
            return []
        baseline_rows = sections_payload.get("positions_baseline", [])
        enrichment_rows = sections_payload.get("instrument_enrichment", [])
        totals_payload = sections_payload.get("portfolio_totals", {})

        if not isinstance(baseline_rows, list):
            return []
        if not isinstance(enrichment_rows, list):
            enrichment_rows = []
        if not isinstance(totals_payload, dict):
            totals_payload = {}

        total_market_value = self._optional_money(
            totals_payload.get("baseline_total_market_value_base")
        )
        if total_market_value is None:
            total_market_value = 0.0

        enrichment_by_security_id = {
            str(item.get("security_id", "")): item
            for item in enrichment_rows
            if isinstance(item, dict) and item.get("security_id") is not None
        }
        rows: list[WorkbenchPositionView] = []
        for item in baseline_rows:
            if not isinstance(item, dict):
                continue
            security_id = str(item.get("security_id", "UNKNOWN"))
            enrichment = enrichment_by_security_id.get(security_id, {})
            market_value_base = self._optional_money(item.get("market_value_base"))
            weight_ratio = item.get("weight")
            weight_pct = self._ratio_to_pct(weight_ratio)
            if weight_pct is None and market_value_base is not None and total_market_value > 0:
                weight_pct = float(
                    quantize_performance((market_value_base / total_market_value) * 100.0)
                )
            rows.append(
                WorkbenchPositionView(
                    security_id=security_id,
                    instrument_name=str(enrichment.get("instrument_name", security_id)),
                    asset_class=(
                        str(enrichment["asset_class"])
                        if enrichment.get("asset_class") is not None
                        else None
                    ),
                    quantity=float(quantize_quantity(item.get("quantity", 0.0))),
                    market_value_base=market_value_base,
                    weight_pct=weight_pct,
                )
            )
        rows.sort(key=lambda row: row.security_id)
        return rows

    def _parse_position_market_value(self, item: dict[str, Any]) -> float | None:
        valuation_payload = item.get("valuation")
        if isinstance(valuation_payload, dict):
            for key in ("market_value_base", "market_value", "current_value_base", "current_value"):
                value = valuation_payload.get(key)
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

    async def _evaluate_policy_feedback(
        self,
        portfolio_id: str,
        session_id: str,
        session_version: int,
        projected_positions: list[WorkbenchProjectedPositionView],
        correlation_id: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> WorkbenchPolicyFeedback:
        overview = await self.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        simulate_payload = {
            "portfolio_snapshot": {
                "portfolio_id": portfolio_id,
                "base_currency": overview.portfolio.base_currency,
                "positions": [
                    {
                        "instrument_id": row.security_id,
                        "quantity": f"{row.proposed_quantity:.4f}",
                    }
                    for row in projected_positions
                    if row.proposed_quantity > 0
                ],
                "cash_balances": [],
            },
            "market_data_snapshot": {"prices": [], "fx_rates": []},
            "shelf_entries": [],
            "options": {
                "enable_proposal_simulation": True,
                "proposal_apply_cash_flows_first": True,
                "proposal_block_negative_cash": True,
            },
            "proposed_cash_flows": [],
            "proposed_trades": [],
        }
        idempotency_key = f"sandbox-{session_id}-{session_version}"
        dpm_status, dpm_payload = await self._dpm_client.simulate_proposal(
            body=simulate_payload,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        if dpm_status >= status.HTTP_400_BAD_REQUEST:
            warnings.append("MANAGE_POLICY_SIMULATION_UNAVAILABLE")
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code=f"HTTP_{dpm_status}",
                    detail=str(dpm_payload.get("detail", dpm_payload)),
                )
            )
            return WorkbenchPolicyFeedback(
                status="UNAVAILABLE",
                detail="Policy simulation unavailable",
                raw=dpm_payload if isinstance(dpm_payload, dict) else None,
            )

        gate_decision = dpm_payload.get("gate_decision")
        if isinstance(gate_decision, dict):
            gate_status = str(gate_decision.get("status", "UNKNOWN"))
            return WorkbenchPolicyFeedback(
                status=gate_status,
                detail=str(gate_decision.get("reason_code", "")) or None,
                raw=dpm_payload,
            )
        return WorkbenchPolicyFeedback(
            status=str(dpm_payload.get("status", "AVAILABLE")),
            detail=None,
            raw=dpm_payload,
        )

    def _parse_lotus_core_snapshot(
        self,
        fallback_portfolio_id: str,
        portfolio_payload: dict[str, Any],
        snapshot_payload: dict[str, Any],
        fallback_as_of_date: str,
    ) -> tuple[WorkbenchPortfolioSummary, WorkbenchOverviewSummary, str]:
        if not isinstance(portfolio_payload, dict) or not isinstance(snapshot_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid lotus-core core snapshot payload structure.",
            )

        sections_payload = snapshot_payload.get("sections", {})
        if not isinstance(sections_payload, dict):
            sections_payload = {}
        baseline_rows = sections_payload.get("positions_baseline", [])
        if not isinstance(baseline_rows, list):
            baseline_rows = []
        portfolio_totals = sections_payload.get("portfolio_totals", {})
        if not isinstance(portfolio_totals, dict):
            portfolio_totals = {}

        total_market_value_value = portfolio_totals.get("baseline_total_market_value_base")
        total_market_value = (
            float(quantize_money(total_market_value_value))
            if total_market_value_value is not None
            else float(
                quantize_money(
                    sum(
                        float(row.get("market_value_base", 0.0))
                        for row in baseline_rows
                        if isinstance(row, dict)
                    )
                )
            )
        )
        total_cash = float(
            quantize_money(
                sum(
                    float(row.get("market_value_base", 0.0))
                    for row in baseline_rows
                    if isinstance(row, dict) and str(row.get("security_id", "")).startswith("CASH")
                )
            )
        )
        cash_weight = 0.0
        if total_market_value > 0:
            cash_weight = float(
                quantize_performance(max(0.0, (total_cash / total_market_value) * 100.0))
            )

        as_of_date = str(snapshot_payload.get("as_of_date", fallback_as_of_date))
        portfolio = WorkbenchPortfolioSummary(
            portfolio_id=str(portfolio_payload.get("portfolio_id", fallback_portfolio_id)).strip()
            or fallback_portfolio_id,
            client_id=(
                str(portfolio_payload["client_id"])
                if portfolio_payload.get("client_id") is not None
                else (
                    str(portfolio_payload["cif_id"])
                    if portfolio_payload.get("cif_id") is not None
                    else None
                )
            ),
            base_currency=str(portfolio_payload.get("base_currency", "USD")),
            booking_center_code=(
                str(portfolio_payload["booking_center_code"])
                if portfolio_payload.get("booking_center_code") is not None
                else None
            ),
        )
        overview = WorkbenchOverviewSummary(
            market_value_base=total_market_value,
            cash_weight_pct=cash_weight,
            position_count=len(baseline_rows),
        )
        return portfolio, overview, as_of_date

    def _parse_performance_snapshot(
        self,
        result: object,
        partial_failures: list[WorkbenchPartialFailure],
        warnings: list[str],
    ) -> WorkbenchPerformanceSnapshot | None:
        if isinstance(result, Exception):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-performance",
                    error_code="UPSTREAM_EXCEPTION",
                    detail=str(result),
                )
            )
            warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
            return None

        if not isinstance(result, tuple) or len(result) != 2:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-performance",
                    error_code="INVALID_UPSTREAM_RESPONSE",
                    detail=f"unexpected result type: {type(result)}",
                )
            )
            warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
            return None

        performance_status, performance_payload = result
        if not isinstance(performance_payload, dict):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-performance",
                    error_code="INVALID_UPSTREAM_PAYLOAD",
                    detail=f"unexpected payload type: {type(performance_payload)}",
                )
            )
            warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
            return None

        if performance_status >= status.HTTP_400_BAD_REQUEST:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-performance",
                    error_code=f"HTTP_{performance_status}",
                    detail=str(performance_payload.get("detail", performance_payload)),
                )
            )
            warnings.append("PERFORMANCE_SNAPSHOT_UNAVAILABLE")
            return None

        results_by_period = performance_payload.get(
            "results_by_period",
            performance_payload.get("resultsByPeriod", {}),
        )
        if not isinstance(results_by_period, dict):
            warnings.append("PERFORMANCE_SNAPSHOT_INVALID")
            return None

        if "YTD" in results_by_period:
            period_key = "YTD"
        else:
            keys = iter(results_by_period)
            try:
                period_key = next(keys)
            except StopIteration:
                return None

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

        return WorkbenchPerformanceSnapshot(
            period=period_key,
            return_pct=period_return_payload.get("base"),
            benchmark_return_pct=None,
        )

    def _optional_money(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(quantize_money(value))
        except (TypeError, ValueError):
            return None

    def _ratio_to_pct(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(quantize_performance(float(value) * 100.0))
        except (TypeError, ValueError):
            return None

    def _parse_dpm_snapshot(
        self,
        result: object,
        partial_failures: list[WorkbenchPartialFailure],
        warnings: list[str],
    ) -> WorkbenchRebalanceSnapshot | None:
        if isinstance(result, Exception):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code="UPSTREAM_EXCEPTION",
                    detail=str(result),
                )
            )
            warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
            return None

        if not isinstance(result, tuple) or len(result) != 2:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code="INVALID_UPSTREAM_RESPONSE",
                    detail=f"unexpected result type: {type(result)}",
                )
            )
            warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
            return None

        dpm_status, dpm_payload = result
        if not isinstance(dpm_payload, dict):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code="INVALID_UPSTREAM_PAYLOAD",
                    detail=f"unexpected payload type: {type(dpm_payload)}",
                )
            )
            warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
            return None

        if dpm_status >= status.HTTP_400_BAD_REQUEST:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-manage",
                    error_code=f"HTTP_{dpm_status}",
                    detail=str(dpm_payload.get("detail", dpm_payload)),
                )
            )
            warnings.append("MANAGE_REBALANCE_UNAVAILABLE")
            return None

        items = dpm_payload.get("items", [])
        if not isinstance(items, list) or not items:
            return WorkbenchRebalanceSnapshot(status="NOT_AVAILABLE")

        latest = items[0]
        if not isinstance(latest, dict):
            return WorkbenchRebalanceSnapshot(status="NOT_AVAILABLE")

        created_at = latest.get("created_at")
        last_run_at_utc = None
        if isinstance(created_at, str):
            last_run_at_utc = created_at
        elif isinstance(created_at, datetime):
            last_run_at_utc = created_at.astimezone(UTC).isoformat()

        return WorkbenchRebalanceSnapshot(
            status=str(latest.get("status", "UNKNOWN")),
            last_rebalance_run_id=(
                str(latest["rebalance_run_id"])
                if latest.get("rebalance_run_id") is not None
                else None
            ),
            last_run_at_utc=last_run_at_utc,
        )
