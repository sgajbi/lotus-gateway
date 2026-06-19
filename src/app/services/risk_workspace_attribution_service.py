from typing import cast

from fastapi import status

from app.contracts.risk_workspace import WorkbenchRiskAttributionResponse
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.domain_client_protocols import RiskWorkspaceClient
from app.services.risk_workspace_attribution import (
    blocked_attribution_response,
    map_attribution_response,
    normalize_risk_attribution_grouping,
    normalize_risk_attribution_type,
    unavailable_attribution,
)
from app.services.risk_workspace_cache import (
    RiskWorkspaceResponse,
    attribution_cache_key,
    with_cache_status,
)
from app.services.risk_workspace_requests import (
    RiskAttributionRequestContext,
    build_attribution_request,
    build_attribution_request_context,
)


class RiskWorkspaceAttributionServiceMixin:
    _cache: AsyncTtlCache[RiskWorkspaceResponse]
    _risk_client: RiskWorkspaceClient

    async def get_attribution(
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
        attribution_type: str,
        grouping_dimension: str,
    ) -> WorkbenchRiskAttributionResponse:
        context = self._risk_attribution_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
            attribution_type=attribution_type,
            grouping_dimension=grouping_dimension,
        )
        blocked_response = self._blocked_risk_attribution_response(context)
        if blocked_response is not None:
            return blocked_response

        return await self._cached_attribution_response(context)

    async def _cached_attribution_response(
        self,
        context: RiskAttributionRequestContext,
    ) -> WorkbenchRiskAttributionResponse:
        async def _load() -> WorkbenchRiskAttributionResponse:
            return await self._load_attribution_response(context)

        response, cache_hit = await self._cache.get_or_set_with_status(
            key=attribution_cache_key(context),
            factory=_load,
        )
        return cast(
            WorkbenchRiskAttributionResponse,
            with_cache_status(
                response,
                correlation_id=context.correlation_id,
                cache_hit=cache_hit,
            ),
        )

    def _risk_attribution_request_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        detail_basis: str,
        benchmark_code: str | None,
        as_of_date: str | None,
        report_start_date: str | None,
        report_end_date: str | None,
        reporting_currency: str | None,
        attribution_type: str,
        grouping_dimension: str,
    ) -> RiskAttributionRequestContext:
        return build_attribution_request_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            period=period,
            detail_basis=detail_basis,
            benchmark_code=benchmark_code,
            as_of_date=as_of_date,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            reporting_currency=reporting_currency,
            attribution_type=normalize_risk_attribution_type(attribution_type),
            grouping_dimension=normalize_risk_attribution_grouping(grouping_dimension),
        )

    def _blocked_risk_attribution_response(
        self,
        context: RiskAttributionRequestContext,
    ) -> WorkbenchRiskAttributionResponse | None:
        return blocked_attribution_response(
            correlation_id=context.correlation_id,
            portfolio_id=context.portfolio_id,
            period=context.period,
            as_of_date=context.as_of_date,
            benchmark_code=context.benchmark_code,
            attribution_type=context.attribution_type,
            grouping_dimension=context.grouping_dimension,
        )

    async def _load_attribution_response(
        self,
        context: RiskAttributionRequestContext,
    ) -> WorkbenchRiskAttributionResponse:
        payload = build_attribution_request(
            portfolio_id=context.portfolio_id,
            period=context.period,
            detail_basis=context.detail_basis,
            benchmark_code=context.benchmark_code,
            as_of_date=context.as_of_date,
            report_start_date=context.report_start_date,
            report_end_date=context.report_end_date,
            reporting_currency=context.reporting_currency,
            attribution_type=context.attribution_type,
            grouping_dimension=context.grouping_dimension,
        )
        (
            upstream_status,
            upstream_payload,
        ) = await self._risk_client.post_risk_historical_attribution(
            payload=payload,
            correlation_id=context.correlation_id,
        )
        if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(upstream_payload, dict):
            return unavailable_attribution(
                correlation_id=context.correlation_id,
                portfolio_id=context.portfolio_id,
                period=context.period,
                as_of_date=context.as_of_date,
                benchmark_code=context.benchmark_code,
                attribution_type=context.attribution_type,
                grouping_dimension=context.grouping_dimension,
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        return map_attribution_response(
            correlation_id=context.correlation_id,
            portfolio_id=context.portfolio_id,
            period=context.period,
            as_of_date=context.as_of_date,
            benchmark_code=context.benchmark_code,
            attribution_type=context.attribution_type,
            grouping_dimension=context.grouping_dimension,
            upstream_payload=upstream_payload,
        )
