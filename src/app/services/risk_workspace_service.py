from typing import Any, cast

from fastapi import status

from app.config import settings
from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.domain_client_protocols import RiskWorkspaceClient
from app.services.risk_workspace_attribution_service import RiskWorkspaceAttributionServiceMixin
from app.services.risk_workspace_cache import (
    RiskWorkspaceResponse,
    concentration_cache_key,
    drawdown_cache_key,
    rolling_cache_key,
    summary_cache_key,
    with_cache_status,
)
from app.services.risk_workspace_concentration import (
    map_concentration_response,
    unavailable_concentration,
)
from app.services.risk_workspace_drawdown import (
    map_drawdown_response,
    unavailable_drawdown,
)
from app.services.risk_workspace_requests import (
    RiskConcentrationRequestContext,
    RiskDrawdownRequestContext,
    RiskRollingRequestContext,
    RiskSummaryRequestContext,
    build_concentration_request,
    build_concentration_request_context,
    build_drawdown_request,
    build_drawdown_request_context,
    build_rolling_request,
    build_rolling_request_context,
    build_summary_request,
    build_summary_request_context,
)
from app.services.risk_workspace_rolling import (
    map_rolling_response,
    rolling_sharpe_failure_reason,
    should_retry_rolling_without_sharpe,
    unavailable_rolling,
)
from app.services.risk_workspace_summary import map_summary_response, unavailable_summary


class RiskWorkspaceService(RiskWorkspaceAttributionServiceMixin):
    def __init__(
        self,
        risk_client: RiskWorkspaceClient,
        *,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self._risk_client = risk_client
        self._cache = AsyncTtlCache[RiskWorkspaceResponse](
            ttl_seconds=cache_ttl_seconds or settings.risk_bff_cache_ttl_seconds
        )

    def clear_cache(self) -> None:
        self._cache.clear()

    async def get_summary(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
    ) -> WorkbenchRiskSummaryResponse:
        context = build_summary_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
        )
        response, cache_hit = await self._cache.get_or_set_with_status(
            key=summary_cache_key(context),
            factory=lambda: self._load_summary_response(context),
        )
        return cast(
            WorkbenchRiskSummaryResponse,
            with_cache_status(
                response,
                correlation_id=correlation_id,
                cache_hit=cache_hit,
            ),
        )

    async def _load_summary_response(
        self,
        context: RiskSummaryRequestContext,
    ) -> WorkbenchRiskSummaryResponse:
        payload = build_summary_request(
            portfolio_id=context.portfolio_id,
            period=context.period,
            detail_basis=context.detail_basis,
            as_of_date=context.as_of_date,
            report_start_date=context.report_start_date,
            report_end_date=context.report_end_date,
            reporting_currency=context.reporting_currency,
        )
        upstream_status, upstream_payload = await self._risk_client.post_risk_calculate(
            payload=payload,
            correlation_id=context.correlation_id,
        )
        if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(upstream_payload, dict):
            return unavailable_summary(
                correlation_id=context.correlation_id,
                portfolio_id=context.portfolio_id,
                period=context.period,
                as_of_date=context.as_of_date,
                benchmark_code=context.benchmark_code,
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        return map_summary_response(
            correlation_id=context.correlation_id,
            portfolio_id=context.portfolio_id,
            period=context.period,
            as_of_date=context.as_of_date,
            benchmark_code=context.benchmark_code,
            upstream_payload=upstream_payload,
        )

    async def get_concentration(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        benchmark_code: str | None,
    ) -> WorkbenchRiskConcentrationResponse:
        context = build_concentration_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
        )

        async def _load() -> WorkbenchRiskConcentrationResponse:
            return await self._load_concentration_response(context)

        response, cache_hit = await self._cache.get_or_set_with_status(
            key=concentration_cache_key(context),
            factory=_load,
        )
        return cast(
            WorkbenchRiskConcentrationResponse,
            with_cache_status(
                response,
                correlation_id=correlation_id,
                cache_hit=cache_hit,
            ),
        )

    async def _load_concentration_response(
        self,
        context: RiskConcentrationRequestContext,
    ) -> WorkbenchRiskConcentrationResponse:
        payload = build_concentration_request(
            portfolio_id=context.portfolio_id,
            as_of_date=context.as_of_date,
            reporting_currency=context.reporting_currency,
        )
        upstream_status, upstream_payload = await self._risk_client.post_risk_concentration(
            payload=payload,
            correlation_id=context.correlation_id,
        )
        if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(upstream_payload, dict):
            return unavailable_concentration(
                correlation_id=context.correlation_id,
                portfolio_id=context.portfolio_id,
                period=context.period,
                as_of_date=context.as_of_date,
                benchmark_code=context.benchmark_code,
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        return map_concentration_response(
            correlation_id=context.correlation_id,
            portfolio_id=context.portfolio_id,
            period=context.period,
            as_of_date=context.as_of_date,
            benchmark_code=context.benchmark_code,
            upstream_payload=upstream_payload,
        )

    async def get_drawdown(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        include_underwater_series: bool,
    ) -> WorkbenchRiskDrawdownResponse:
        context = build_drawdown_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
            include_underwater_series=include_underwater_series,
        )

        async def _load() -> WorkbenchRiskDrawdownResponse:
            return await self._load_drawdown_response(context)

        response, cache_hit = await self._cache.get_or_set_with_status(
            key=drawdown_cache_key(context),
            factory=_load,
        )
        return cast(
            WorkbenchRiskDrawdownResponse,
            with_cache_status(
                response,
                correlation_id=correlation_id,
                cache_hit=cache_hit,
            ),
        )

    async def _load_drawdown_response(
        self,
        context: RiskDrawdownRequestContext,
    ) -> WorkbenchRiskDrawdownResponse:
        payload = build_drawdown_request(
            portfolio_id=context.portfolio_id,
            period=context.period,
            detail_basis=context.detail_basis,
            benchmark_code=context.benchmark_code,
            as_of_date=context.as_of_date,
            report_start_date=context.report_start_date,
            report_end_date=context.report_end_date,
            reporting_currency=context.reporting_currency,
            include_underwater_series=context.include_underwater_series,
        )
        upstream_status, upstream_payload = await self._risk_client.post_risk_drawdown(
            payload=payload,
            correlation_id=context.correlation_id,
        )
        if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(upstream_payload, dict):
            return unavailable_drawdown(
                correlation_id=context.correlation_id,
                portfolio_id=context.portfolio_id,
                period=context.period,
                as_of_date=context.as_of_date,
                benchmark_code=context.benchmark_code,
                include_underwater_series=context.include_underwater_series,
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        return map_drawdown_response(
            correlation_id=context.correlation_id,
            portfolio_id=context.portfolio_id,
            period=context.period,
            as_of_date=context.as_of_date,
            benchmark_code=context.benchmark_code,
            include_underwater_series=context.include_underwater_series,
            upstream_payload=upstream_payload,
        )

    async def get_rolling(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None = None,
        report_end_date: str | None = None,
        reporting_currency: str | None,
        include_time_series: bool,
    ) -> WorkbenchRiskRollingResponse:
        context = build_rolling_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
            include_time_series=include_time_series,
        )

        async def _load() -> WorkbenchRiskRollingResponse:
            return await self._load_rolling_response(context)

        response, cache_hit = await self._cache.get_or_set_with_status(
            key=rolling_cache_key(context),
            factory=_load,
        )
        return cast(
            WorkbenchRiskRollingResponse,
            with_cache_status(
                response,
                correlation_id=correlation_id,
                cache_hit=cache_hit,
            ),
        )

    async def _load_rolling_response(
        self,
        context: RiskRollingRequestContext,
    ) -> WorkbenchRiskRollingResponse:
        upstream_status, upstream_payload = await self._post_rolling_metrics(
            context=context,
            include_sharpe=True,
        )
        sharpe_fallback_reason: str | None = None
        if should_retry_rolling_without_sharpe(
            upstream_status=upstream_status,
            upstream_payload=upstream_payload,
        ):
            sharpe_fallback_reason = rolling_sharpe_failure_reason(upstream_payload)
            upstream_status, upstream_payload = await self._post_rolling_metrics(
                context=context,
                include_sharpe=False,
            )

        if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(upstream_payload, dict):
            return unavailable_rolling(
                correlation_id=context.correlation_id,
                portfolio_id=context.portfolio_id,
                period=context.period,
                as_of_date=context.as_of_date,
                benchmark_code=context.benchmark_code,
                include_time_series=context.include_time_series,
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )

        return map_rolling_response(
            correlation_id=context.correlation_id,
            portfolio_id=context.portfolio_id,
            period=context.period,
            as_of_date=context.as_of_date,
            benchmark_code=context.benchmark_code,
            include_time_series=context.include_time_series,
            sharpe_fallback_reason=sharpe_fallback_reason,
            upstream_payload=upstream_payload,
        )

    async def _post_rolling_metrics(
        self,
        *,
        context: RiskRollingRequestContext,
        include_sharpe: bool,
    ) -> tuple[int, Any]:
        payload = build_rolling_request(
            portfolio_id=context.portfolio_id,
            period=context.period,
            detail_basis=context.detail_basis,
            benchmark_code=context.benchmark_code,
            as_of_date=context.as_of_date,
            report_start_date=context.report_start_date,
            report_end_date=context.report_end_date,
            reporting_currency=context.reporting_currency,
            include_time_series=context.include_time_series,
            include_sharpe=include_sharpe,
        )
        return await self._risk_client.post_risk_rolling_metrics(
            payload=payload,
            correlation_id=context.correlation_id,
        )
