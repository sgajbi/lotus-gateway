from datetime import date, timedelta
from typing import Any, cast

from fastapi import status

from app.config import settings
from app.contracts.risk_workspace import (
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.services.async_ttl_cache import AsyncTtlCache
from app.services.domain_client_protocols import RiskWorkspaceClient
from app.services.risk_workspace_attribution import (
    blocked_attribution_response,
    map_attribution_response,
    normalize_risk_attribution_grouping,
    normalize_risk_attribution_type,
    unavailable_attribution,
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
    build_attribution_request,
    build_concentration_request,
    build_drawdown_request,
    build_risk_periods,
    build_rolling_request,
    build_summary_request,
    normalize_period,
    resolve_reporting_currency,
)
from app.services.risk_workspace_rolling import (
    map_rolling_response,
    rolling_sharpe_failure_reason,
    should_retry_rolling_without_sharpe,
    unavailable_rolling,
)
from app.services.risk_workspace_summary import (
    map_summary_response,
    unavailable_summary,
)


class RiskWorkspaceService:
    def __init__(
        self,
        risk_client: RiskWorkspaceClient,
        *,
        cache_ttl_seconds: float | None = None,
    ) -> None:
        self._risk_client = risk_client
        self._cache = AsyncTtlCache[
            WorkbenchRiskSummaryResponse
            | WorkbenchRiskConcentrationResponse
            | WorkbenchRiskDrawdownResponse
            | WorkbenchRiskRollingResponse
            | WorkbenchRiskAttributionResponse
        ](ttl_seconds=cache_ttl_seconds or settings.risk_bff_cache_ttl_seconds)

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
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "summary",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
        )

        async def _load() -> WorkbenchRiskSummaryResponse:
            payload = build_summary_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_calculate(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_summary(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return map_summary_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskSummaryResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
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
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "concentration",
            portfolio_id,
            period,
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            benchmark_code or "",
        )

        async def _load() -> WorkbenchRiskConcentrationResponse:
            payload = build_concentration_request(
                portfolio_id=portfolio_id,
                as_of_date=resolved_as_of_date,
                reporting_currency=reporting_currency,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_concentration(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_concentration(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return map_concentration_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskConcentrationResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
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
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "drawdown",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            include_underwater_series,
        )

        async def _load() -> WorkbenchRiskDrawdownResponse:
            payload = build_drawdown_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                include_underwater_series=include_underwater_series,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_drawdown(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_drawdown(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    include_underwater_series=include_underwater_series,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return map_drawdown_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                include_underwater_series=include_underwater_series,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskDrawdownResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
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
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        cache_key = (
            "rolling",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            include_time_series,
        )

        async def _load() -> WorkbenchRiskRollingResponse:
            initial_payload = build_rolling_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                include_time_series=include_time_series,
                include_sharpe=True,
            )
            upstream_status, upstream_payload = await self._risk_client.post_risk_rolling_metrics(
                payload=initial_payload,
                correlation_id=correlation_id,
            )
            sharpe_fallback_reason: str | None = None
            if should_retry_rolling_without_sharpe(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            ):
                sharpe_fallback_reason = rolling_sharpe_failure_reason(upstream_payload)
                fallback_payload = build_rolling_request(
                    portfolio_id=portfolio_id,
                    period=period,
                    detail_basis=detail_basis,
                    benchmark_code=benchmark_code,
                    as_of_date=resolved_as_of_date,
                    report_start_date=report_start_date,
                    report_end_date=report_end_date,
                    reporting_currency=reporting_currency,
                    include_time_series=include_time_series,
                    include_sharpe=False,
                )
                (
                    upstream_status,
                    upstream_payload,
                ) = await self._risk_client.post_risk_rolling_metrics(
                    payload=fallback_payload,
                    correlation_id=correlation_id,
                )

            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_rolling(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    include_time_series=include_time_series,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )

            return map_rolling_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                include_time_series=include_time_series,
                sharpe_fallback_reason=sharpe_fallback_reason,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskRollingResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )

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
        resolved_as_of_date = _resolve_as_of_date(as_of_date)
        normalized_type = _normalize_risk_attribution_type(attribution_type)
        normalized_grouping = _normalize_risk_attribution_grouping(grouping_dimension)
        blocked_response = blocked_attribution_response(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            period=period,
            as_of_date=resolved_as_of_date,
            benchmark_code=benchmark_code,
            attribution_type=normalized_type,
            grouping_dimension=normalized_grouping,
        )
        if blocked_response is not None:
            return blocked_response

        cache_key = (
            "attribution",
            portfolio_id,
            period,
            detail_basis,
            benchmark_code or "",
            resolved_as_of_date,
            report_start_date or "",
            report_end_date or "",
            reporting_currency or "",
            normalized_type,
            normalized_grouping,
        )

        async def _load() -> WorkbenchRiskAttributionResponse:
            payload = build_attribution_request(
                portfolio_id=portfolio_id,
                period=period,
                detail_basis=detail_basis,
                benchmark_code=benchmark_code,
                as_of_date=resolved_as_of_date,
                report_start_date=report_start_date,
                report_end_date=report_end_date,
                reporting_currency=reporting_currency,
                attribution_type=normalized_type,
                grouping_dimension=normalized_grouping,
            )
            (
                upstream_status,
                upstream_payload,
            ) = await self._risk_client.post_risk_historical_attribution(
                payload=payload,
                correlation_id=correlation_id,
            )
            if upstream_status >= status.HTTP_400_BAD_REQUEST or not isinstance(
                upstream_payload, dict
            ):
                return unavailable_attribution(
                    correlation_id=correlation_id,
                    portfolio_id=portfolio_id,
                    period=period,
                    as_of_date=resolved_as_of_date,
                    benchmark_code=benchmark_code,
                    attribution_type=normalized_type,
                    grouping_dimension=normalized_grouping,
                    upstream_status=upstream_status,
                    upstream_payload=upstream_payload,
                )
            return map_attribution_response(
                correlation_id=correlation_id,
                portfolio_id=portfolio_id,
                period=period,
                as_of_date=resolved_as_of_date,
                benchmark_code=benchmark_code,
                attribution_type=normalized_type,
                grouping_dimension=normalized_grouping,
                upstream_payload=upstream_payload,
            )

        response, cache_hit = await self._cache.get_or_set_with_status(key=cache_key, factory=_load)
        typed_response = cast(WorkbenchRiskAttributionResponse, response)
        return typed_response.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": typed_response.metadata.model_copy(
                    update={"cache_status": "hit" if cache_hit else "miss"}
                ),
            },
            deep=True,
        )


def _resolve_reporting_currency(value: str | None) -> str:
    return resolve_reporting_currency(value)


def _normalize_risk_attribution_type(value: str) -> str:
    return normalize_risk_attribution_type(value)


def _normalize_risk_attribution_grouping(value: str) -> str:
    return normalize_risk_attribution_grouping(value)


def _latest_business_day(today: date | None = None) -> date:
    resolved_today = today or date.today()
    if resolved_today.weekday() == 5:
        return resolved_today - timedelta(days=1)
    if resolved_today.weekday() == 6:
        return resolved_today - timedelta(days=2)
    return resolved_today


def _resolve_as_of_date(value: str | None) -> str:
    return value or _latest_business_day().isoformat()


def _normalize_period(value: str) -> str:
    return normalize_period(value)


def _build_risk_periods(
    *,
    period: str,
    report_start_date: str | None,
    report_end_date: str | None,
) -> list[dict[str, Any]]:
    return build_risk_periods(
        period=period,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
    )
