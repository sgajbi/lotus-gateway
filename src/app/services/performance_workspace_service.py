from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Any

from app.clients.lotus_analytics_client import LotusAnalyticsClient
from app.clients.lotus_core_query_client import LotusCoreQueryClient
from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionRowView,
    AttributionSummaryView,
    ContributionLevelView,
    ContributionRowView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceChartPoint,
    PerformanceComparativeSummary,
    PerformanceWorkspaceResponse,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.precision_policy import quantize_performance
from app.services.workbench_service import WorkbenchService


class PerformanceWorkspaceService:
    def __init__(
        self,
        workbench_service: WorkbenchService,
        analytics_client: LotusAnalyticsClient,
        lotus_core_query_client: LotusCoreQueryClient,
    ):
        self._workbench_service = workbench_service
        self._analytics_client = analytics_client
        self._lotus_core_query_client = lotus_core_query_client

    async def get_performance_workspace(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        detail_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
    ) -> PerformanceWorkspaceResponse:
        overview = await self._workbench_service.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        warnings = list(overview.warnings)
        partial_failures = list(overview.partial_failures)
        report_end_date = await self._resolve_report_end_date(
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            correlation_id=correlation_id,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        report_start_date = self._resolve_report_start_date(
            as_of_date=date.fromisoformat(report_end_date),
            period=period,
        )

        net_twr_task = self._analytics_client.get_twr_analytics(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            period=period,
            metric_basis="NET",
            benchmark_id=benchmark_code,
            correlation_id=correlation_id,
        )
        gross_twr_task = self._analytics_client.get_twr_analytics(
            portfolio_id=portfolio_id,
            report_end_date=report_end_date,
            period=period,
            metric_basis="GROSS",
            benchmark_id=benchmark_code,
            correlation_id=correlation_id,
        )
        mwr_task = self._analytics_client.get_mwr_analytics(
            portfolio_id=portfolio_id,
            as_of_date=report_end_date,
            window_start_date=report_start_date.isoformat(),
            correlation_id=correlation_id,
        )
        contribution_task = self._analytics_client.get_contribution_analytics(
            portfolio_id=portfolio_id,
            report_start_date=report_start_date.isoformat(),
            report_end_date=report_end_date,
            period=period,
            metric_basis=detail_basis,
            dimension=detail_dimension,
            correlation_id=correlation_id,
        )
        attribution_task = (
            self._analytics_client.get_attribution_analytics(
                portfolio_id=portfolio_id,
                report_start_date=report_start_date.isoformat(),
                report_end_date=report_end_date,
                period=period,
                metric_basis=detail_basis,
                benchmark_id=benchmark_code,
                dimension=detail_dimension,
                correlation_id=correlation_id,
            )
            if benchmark_code
            else self._empty_async_result()
        )

        results = await asyncio.gather(
            net_twr_task,
            gross_twr_task,
            mwr_task,
            contribution_task,
            attribution_task,
            return_exceptions=True,
        )

        net_performance, net_chart = self._parse_twr_result(
            result=results[0],
            metric_basis="NET",
            chart_frequency=chart_frequency,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        gross_performance, gross_chart = self._parse_twr_result(
            result=results[1],
            metric_basis="GROSS",
            chart_frequency=chart_frequency,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        money_weighted_return = self._parse_mwr_result(
            result=results[2],
            warnings=warnings,
            partial_failures=partial_failures,
        )
        contribution = self._parse_contribution_result(
            result=results[3],
            metric_basis=detail_basis,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        attribution = self._parse_attribution_result(
            result=results[4],
            metric_basis=detail_basis,
            warnings=warnings,
            partial_failures=partial_failures,
        )

        return PerformanceWorkspaceResponse(
            correlation_id=correlation_id,
            contract_version=overview.contract_version,
            portfolio_id=portfolio_id,
            as_of_date=overview.as_of_date,
            period=period,
            chart_frequency=chart_frequency,
            detail_dimension=detail_dimension,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            portfolio=overview.portfolio,
            overview=overview.overview,
            net_performance=net_performance,
            gross_performance=gross_performance,
            money_weighted_return=money_weighted_return,
            net_chart=net_chart,
            gross_chart=gross_chart,
            contribution=contribution,
            attribution=attribution,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _resolve_report_end_date(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> str:
        status_code, payload = await (
            self._lotus_core_query_client.get_portfolio_analytics_reference(
                portfolio_id=portfolio_id,
                as_of_date=as_of_date,
                consumer_system="lotus-gateway",
                correlation_id=correlation_id,
            )
        )
        if status_code >= 400 or not isinstance(payload, dict):
            warnings.append("PERFORMANCE_REFERENCE_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-core",
                    (
                        f"HTTP_{status_code}"
                        if isinstance(status_code, int)
                        else "INVALID_RESPONSE"
                    ),
                    (
                        str(payload.get("detail", payload))
                        if isinstance(payload, dict)
                        else str(payload)
                    ),
                )
            )
            return as_of_date

        performance_end_date = payload.get("performance_end_date")
        if not isinstance(performance_end_date, str) or not performance_end_date:
            warnings.append("PERFORMANCE_REFERENCE_MISSING_END_DATE")
            return as_of_date
        return performance_end_date

    async def _empty_async_result(self) -> tuple[int, dict[str, Any]]:
        return 204, {}

    def _resolve_report_start_date(self, *, as_of_date: date, period: str) -> date:
        normalized_period = period.upper()
        if normalized_period == "MTD":
            return as_of_date.replace(day=1)
        if normalized_period == "QTD":
            quarter_month = ((as_of_date.month - 1) // 3) * 3 + 1
            return as_of_date.replace(month=quarter_month, day=1)
        if normalized_period == "YTD":
            return as_of_date.replace(month=1, day=1)
        if normalized_period == "1Y":
            return self._shift_years(as_of_date, 1)
        if normalized_period == "3Y":
            return self._shift_years(as_of_date, 3)
        if normalized_period == "5Y":
            return self._shift_years(as_of_date, 5)
        return as_of_date.replace(month=1, day=1)

    def _shift_years(self, anchor: date, years: int) -> date:
        try:
            return anchor.replace(year=anchor.year - years) + timedelta(days=1)
        except ValueError:
            return anchor.replace(month=2, day=28, year=anchor.year - years) + timedelta(days=1)

    def _parse_twr_result(
        self,
        *,
        result: object,
        metric_basis: str,
        chart_frequency: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> tuple[PerformanceComparativeSummary, list[PerformanceChartPoint]]:
        empty_summary = PerformanceComparativeSummary(metric_basis=metric_basis)
        if isinstance(result, Exception):
            warnings.append(f"{metric_basis}_PERFORMANCE_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return empty_summary, []
        status_code, payload = result
        if status_code == 204:
            return None
        if not isinstance(payload, dict):
            warnings.append(f"{metric_basis}_PERFORMANCE_INVALID")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    "INVALID_UPSTREAM_PAYLOAD",
                    f"unexpected payload type: {type(payload)}",
                )
            )
            return empty_summary, []
        if status_code >= 400:
            warnings.append(f"{metric_basis}_PERFORMANCE_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return empty_summary, []

        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            warnings.append(f"{metric_basis}_PERFORMANCE_INVALID")
            return empty_summary, []
        period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period))
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return empty_summary, []

        benchmark_context = payload.get("benchmark_context", {})
        if not isinstance(benchmark_context, dict):
            benchmark_context = {}

        portfolio_block = period_payload.get("portfolio", {})
        benchmark_block = period_payload.get("benchmark", {})
        relative_block = period_payload.get("relative_performance", {})
        summary = PerformanceComparativeSummary(
            metric_basis=metric_basis,
            portfolio_return_pct=self._extract_return(
                portfolio_block, "summary", "period_return", "base"
            ),
            benchmark_return_pct=self._extract_return(
                benchmark_block, "summary", "period_return", "base"
            ),
            active_return_pct=self._extract_return(
                relative_block, "summary", "period_return", "base"
            ),
            annualized_return_pct=self._extract_return(
                portfolio_block, "summary", "annualized_return", "base"
            ),
            benchmark_id=self._safe_str(benchmark_context.get("benchmark_id")),
            benchmark_return_source=self._safe_str(benchmark_context.get("return_source")),
        )
        chart_points = self._parse_chart_points(
            portfolio_block=portfolio_block,
            benchmark_block=benchmark_block,
            relative_block=relative_block,
            chart_frequency=chart_frequency,
        )
        return summary, chart_points

    def _parse_chart_points(
        self,
        *,
        portfolio_block: dict[str, Any],
        benchmark_block: dict[str, Any],
        relative_block: dict[str, Any],
        chart_frequency: str,
    ) -> list[PerformanceChartPoint]:
        normalized_frequency = chart_frequency.lower()
        portfolio_breakdowns = portfolio_block.get("breakdowns", {})
        benchmark_breakdowns = benchmark_block.get("breakdowns", {})
        relative_breakdowns = relative_block.get("breakdowns", {})
        if not isinstance(portfolio_breakdowns, dict):
            return []
        portfolio_rows = portfolio_breakdowns.get(normalized_frequency, [])
        benchmark_rows = (
            benchmark_breakdowns.get(normalized_frequency, [])
            if isinstance(benchmark_breakdowns, dict)
            else []
        )
        relative_rows = (
            relative_breakdowns.get(normalized_frequency, [])
            if isinstance(relative_breakdowns, dict)
            else []
        )
        if not isinstance(portfolio_rows, list):
            return []
        points: list[PerformanceChartPoint] = []
        for index, portfolio_row in enumerate(portfolio_rows):
            if not isinstance(portfolio_row, dict):
                continue
            benchmark_row = benchmark_rows[index] if index < len(benchmark_rows) else {}
            relative_row = relative_rows[index] if index < len(relative_rows) else {}
            if not isinstance(benchmark_row, dict):
                benchmark_row = {}
            if not isinstance(relative_row, dict):
                relative_row = {}
            points.append(
                PerformanceChartPoint(
                    label=str(portfolio_row.get("period", f"point-{index + 1}")),
                    frequency=normalized_frequency,
                    period_start=self._safe_str(portfolio_row.get("period_start")),
                    period_end=self._safe_str(portfolio_row.get("period_end")),
                    portfolio_return_pct=self._extract_nested_return(
                        portfolio_row, "period_return", "base"
                    ),
                    benchmark_return_pct=self._extract_nested_return(
                        benchmark_row, "period_return", "base"
                    ),
                    active_return_pct=self._extract_nested_return(
                        relative_row, "period_return", "base"
                    ),
                    cumulative_portfolio_return_pct=self._extract_nested_return(
                        portfolio_row, "cumulative_return", "base"
                    ),
                    cumulative_benchmark_return_pct=self._extract_nested_return(
                        benchmark_row, "cumulative_return", "base"
                    ),
                    cumulative_active_return_pct=self._extract_nested_return(
                        relative_row, "cumulative_return", "base"
                    ),
                )
            )
        return points

    def _parse_mwr_result(
        self,
        *,
        result: object,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> MoneyWeightedReturnSummary | None:
        if isinstance(result, Exception):
            warnings.append("MWR_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("MWR_INVALID")
            return None
        if status_code >= 400:
            warnings.append("MWR_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        notes = payload.get("notes", [])
        return MoneyWeightedReturnSummary(
            money_weighted_return_pct=self._quantize_optional(payload.get("money_weighted_return")),
            annualized_return_pct=self._quantize_optional(payload.get("mwr_annualized")),
            method=self._safe_str(payload.get("method")),
            start_date=self._safe_str(payload.get("start_date")),
            end_date=self._safe_str(payload.get("end_date")),
            notes=[str(note) for note in notes] if isinstance(notes, list) else [],
        )

    def _parse_contribution_result(
        self,
        *,
        result: object,
        metric_basis: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> ContributionSummaryView | None:
        if isinstance(result, Exception):
            warnings.append("CONTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("CONTRIBUTION_INVALID")
            return None
        if status_code >= 400:
            warnings.append("CONTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None
        period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period))
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        summary_payload = period_payload.get("summary", {})
        levels_payload = period_payload.get("levels", [])
        if not isinstance(summary_payload, dict):
            summary_payload = {}
        levels: list[ContributionLevelView] = []
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                rows: list[ContributionRowView] = []
                row_payloads = level_payload.get("rows", [])
                if isinstance(row_payloads, list):
                    for row_payload in row_payloads[:10]:
                        if not isinstance(row_payload, dict):
                            continue
                        rows.append(
                            ContributionRowView(
                                key_label=self._format_key_label(row_payload.get("key")),
                                contribution_pct=float(
                                    quantize_performance(row_payload.get("contribution", 0.0))
                                ),
                                weight_avg_pct=self._ratio_to_pct(row_payload.get("weight_avg")),
                                local_contribution_pct=self._quantize_optional(
                                    row_payload.get("local_contribution")
                                ),
                                fx_contribution_pct=self._quantize_optional(
                                    row_payload.get("fx_contribution")
                                ),
                                is_other=bool(row_payload.get("is_other", False)),
                            )
                        )
                levels.append(
                    ContributionLevelView(
                        level=int(level_payload.get("level", len(levels) + 1)),
                        name=str(level_payload.get("name", "Level")),
                        rows=rows,
                        total_contribution_pct=(
                            sum(row.contribution_pct for row in rows) if rows else None
                        ),
                    )
                )
        return ContributionSummaryView(
            metric_basis=metric_basis,
            weighting_scheme=self._safe_str(summary_payload.get("weighting_scheme")),
            portfolio_contribution_pct=self._quantize_optional(
                summary_payload.get("portfolio_contribution")
            ),
            total_portfolio_return_pct=self._quantize_optional(
                period_payload.get("total_portfolio_return")
            ),
            coverage_mv_pct=self._quantize_optional(summary_payload.get("coverage_mv_pct")),
            levels=levels,
        )

    def _parse_attribution_result(
        self,
        *,
        result: object,
        metric_basis: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> AttributionSummaryView | None:
        if isinstance(result, Exception):
            warnings.append("ATTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure("lotus-performance", "UPSTREAM_EXCEPTION", str(result))
            )
            return None
        status_code, payload = result
        if not isinstance(payload, dict):
            warnings.append("ATTRIBUTION_INVALID")
            return None
        if status_code >= 400:
            warnings.append("ATTRIBUTION_UNAVAILABLE")
            partial_failures.append(
                self._performance_failure(
                    "lotus-performance",
                    f"HTTP_{status_code}",
                    str(payload.get("detail", payload)),
                )
            )
            return None
        results_by_period = payload.get("results_by_period", {})
        if not isinstance(results_by_period, dict) or not results_by_period:
            return None
        period_key = "YTD" if "YTD" in results_by_period else next(iter(results_by_period))
        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None
        reconciliation_payload = period_payload.get("reconciliation", {})
        benchmark_context = payload.get("benchmark_context", {})
        levels_payload = period_payload.get("levels", [])
        if not isinstance(reconciliation_payload, dict):
            reconciliation_payload = {}
        if not isinstance(benchmark_context, dict):
            benchmark_context = {}
        levels: list[AttributionLevelView] = []
        if isinstance(levels_payload, list):
            for level_payload in levels_payload:
                if not isinstance(level_payload, dict):
                    continue
                groups = level_payload.get("groups", [])
                rows: list[AttributionRowView] = []
                if isinstance(groups, list):
                    for group_payload in groups[:10]:
                        if not isinstance(group_payload, dict):
                            continue
                        rows.append(
                            AttributionRowView(
                                key_label=self._format_key_label(group_payload.get("key")),
                                allocation_pct=float(
                                    quantize_performance(group_payload.get("allocation", 0.0))
                                ),
                                selection_pct=float(
                                    quantize_performance(group_payload.get("selection", 0.0))
                                ),
                                interaction_pct=float(
                                    quantize_performance(group_payload.get("interaction", 0.0))
                                ),
                                total_effect_pct=float(
                                    quantize_performance(group_payload.get("total_effect", 0.0))
                                ),
                            )
                        )
                totals_payload = level_payload.get("totals", {})
                total_effect = None
                if isinstance(totals_payload, dict):
                    total_effect = self._quantize_optional(totals_payload.get("total_effect"))
                levels.append(
                    AttributionLevelView(
                        dimension=str(level_payload.get("dimension", "Dimension")),
                        total_effect_pct=total_effect or 0.0,
                        rows=rows,
                    )
                )
        return AttributionSummaryView(
            metric_basis=metric_basis,
            model=self._safe_str(payload.get("model")),
            linking=self._safe_str(payload.get("linking")),
            benchmark_id=self._safe_str(benchmark_context.get("benchmark_id")),
            active_return_pct=self._quantize_optional(
                reconciliation_payload.get("total_active_return")
            ),
            sum_of_effects_pct=self._quantize_optional(
                reconciliation_payload.get("sum_of_effects")
            ),
            residual_pct=self._quantize_optional(reconciliation_payload.get("residual")),
            levels=levels,
        )

    def _extract_return(self, payload: Any, *path: str) -> float | None:
        current = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return self._quantize_optional(current)

    def _extract_nested_return(self, payload: Any, *path: str) -> float | None:
        current = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return self._quantize_optional(current)

    def _quantize_optional(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(quantize_performance(value))
        except (TypeError, ValueError):
            return None

    def _ratio_to_pct(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(quantize_performance(float(value) * 100.0))
        except (TypeError, ValueError):
            return None

    def _format_key_label(self, payload: Any) -> str:
        if isinstance(payload, dict) and payload:
            return " / ".join(str(value) for value in payload.values())
        return "Unclassified"

    def _safe_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def _performance_failure(
        self,
        source_service: str,
        error_code: str,
        detail: str,
    ) -> WorkbenchPartialFailure:
        return WorkbenchPartialFailure(
            source_service=source_service,
            error_code=error_code,
            detail=detail,
        )
