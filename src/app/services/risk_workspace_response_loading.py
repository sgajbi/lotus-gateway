from __future__ import annotations

from typing import Any

from fastapi import status

from app.contracts.risk_workspace import (
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.services.domain_client_protocols import RiskWorkspaceClient
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
    build_drawdown_request,
    build_rolling_request,
    build_summary_request,
)
from app.services.risk_workspace_rolling import (
    map_rolling_response,
    rolling_sharpe_failure_reason,
    should_retry_rolling_without_sharpe,
    unavailable_rolling,
)
from app.services.risk_workspace_summary import map_summary_response, unavailable_summary


async def load_summary_response(
    *,
    risk_client: RiskWorkspaceClient,
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
    upstream_status, upstream_payload = await risk_client.post_risk_calculate(
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


async def load_concentration_response(
    *,
    risk_client: RiskWorkspaceClient,
    context: RiskConcentrationRequestContext,
) -> WorkbenchRiskConcentrationResponse:
    payload = build_concentration_request(
        portfolio_id=context.portfolio_id,
        as_of_date=context.as_of_date,
        reporting_currency=context.reporting_currency,
    )
    upstream_status, upstream_payload = await risk_client.post_risk_concentration(
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


async def load_drawdown_response(
    *,
    risk_client: RiskWorkspaceClient,
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
    upstream_status, upstream_payload = await risk_client.post_risk_drawdown(
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


async def load_rolling_response(
    *,
    risk_client: RiskWorkspaceClient,
    context: RiskRollingRequestContext,
) -> WorkbenchRiskRollingResponse:
    upstream_status, upstream_payload = await post_rolling_metrics(
        risk_client=risk_client,
        context=context,
        include_sharpe=True,
    )
    sharpe_fallback_reason: str | None = None
    if should_retry_rolling_without_sharpe(
        upstream_status=upstream_status,
        upstream_payload=upstream_payload,
    ):
        sharpe_fallback_reason = rolling_sharpe_failure_reason(upstream_payload)
        upstream_status, upstream_payload = await post_rolling_metrics(
            risk_client=risk_client,
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


async def post_rolling_metrics(
    *,
    risk_client: RiskWorkspaceClient,
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
    return await risk_client.post_risk_rolling_metrics(
        payload=payload,
        correlation_id=context.correlation_id,
    )
