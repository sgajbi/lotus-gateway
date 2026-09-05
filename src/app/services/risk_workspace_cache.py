from typing import TypeVar

from app.contracts.risk_workspace import (
    WorkbenchRiskAttributionResponse,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskDrawdownResponse,
    WorkbenchRiskModuleEnvelope,
    WorkbenchRiskRollingResponse,
    WorkbenchRiskSummaryResponse,
)
from app.middleware.caller_identity import admitted_tenant_cache_scope
from app.services.risk_workspace_requests import (
    RiskAttributionRequestContext,
    RiskConcentrationRequestContext,
    RiskDrawdownRequestContext,
    RiskRollingRequestContext,
    RiskSummaryRequestContext,
)

RiskWorkspaceResponse = (
    WorkbenchRiskSummaryResponse
    | WorkbenchRiskConcentrationResponse
    | WorkbenchRiskDrawdownResponse
    | WorkbenchRiskRollingResponse
    | WorkbenchRiskAttributionResponse
)
RiskWorkspaceResponseT = TypeVar("RiskWorkspaceResponseT", bound=WorkbenchRiskModuleEnvelope)


def summary_cache_key(context: RiskSummaryRequestContext) -> tuple[object, ...]:
    # Risk mandate composition reads Core-backed facts under the admitted
    # tenant fence; one tenant's cached response must never serve another.
    return (
        "summary",
        admitted_tenant_cache_scope(),
        context.portfolio_id,
        context.period,
        context.detail_basis,
        context.benchmark_code or "",
        context.as_of_date,
        context.report_start_date or "",
        context.report_end_date or "",
        context.reporting_currency or "",
    )


def concentration_cache_key(context: RiskConcentrationRequestContext) -> tuple[object, ...]:
    return (
        "concentration",
        admitted_tenant_cache_scope(),
        context.portfolio_id,
        context.period,
        context.as_of_date,
        context.report_start_date or "",
        context.report_end_date or "",
        context.reporting_currency or "",
        context.benchmark_code or "",
    )


def drawdown_cache_key(context: RiskDrawdownRequestContext) -> tuple[object, ...]:
    return (
        "drawdown",
        context.portfolio_id,
        context.period,
        context.detail_basis,
        context.benchmark_code or "",
        context.as_of_date,
        context.report_start_date or "",
        context.report_end_date or "",
        context.reporting_currency or "",
        context.include_underwater_series,
    )


def rolling_cache_key(context: RiskRollingRequestContext) -> tuple[object, ...]:
    return (
        "rolling",
        context.portfolio_id,
        context.period,
        context.detail_basis,
        context.benchmark_code or "",
        context.as_of_date,
        context.report_start_date or "",
        context.report_end_date or "",
        context.reporting_currency or "",
        context.include_time_series,
    )


def attribution_cache_key(context: RiskAttributionRequestContext) -> tuple[object, ...]:
    return (
        "attribution",
        context.portfolio_id,
        context.period,
        context.detail_basis,
        context.benchmark_code or "",
        context.as_of_date,
        context.report_start_date or "",
        context.report_end_date or "",
        context.reporting_currency or "",
        context.attribution_type,
        context.grouping_dimension,
    )


def with_cache_status(
    response: RiskWorkspaceResponseT,
    *,
    correlation_id: str,
    cache_hit: bool,
) -> RiskWorkspaceResponseT:
    return response.model_copy(
        update={
            "correlation_id": correlation_id,
            "metadata": response.metadata.model_copy(
                update={"cache_status": "hit" if cache_hit else "miss"}
            ),
        },
        deep=True,
    )
