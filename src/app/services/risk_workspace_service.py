from typing import cast

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
from app.services.risk_workspace_requests import (
    build_concentration_request_context,
    build_drawdown_request_context,
    build_rolling_request_context,
    build_summary_request_context,
)
from app.services.risk_workspace_response_loading import (
    load_concentration_response,
    load_drawdown_response,
    load_rolling_response,
    load_summary_response,
)


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
            factory=lambda: load_summary_response(
                risk_client=self._risk_client,
                context=context,
            ),
        )
        return cast(
            WorkbenchRiskSummaryResponse,
            with_cache_status(
                response,
                correlation_id=correlation_id,
                cache_hit=cache_hit,
            ),
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
            return await load_concentration_response(
                risk_client=self._risk_client,
                context=context,
            )

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
            return await load_drawdown_response(
                risk_client=self._risk_client,
                context=context,
            )

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
            return await load_rolling_response(
                risk_client=self._risk_client,
                context=context,
            )

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
