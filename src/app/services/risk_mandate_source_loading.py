import asyncio
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.services.risk_mandate_client_protocols import (
    RiskMandateCashSource,
    RiskMandateManageClient,
)
from app.services.risk_mandate_sources import (
    ManageMandateHealthSource,
    ManageMandateSource,
    RiskMandateSources,
    WorkbenchCashMeasureSource,
)


@dataclass(frozen=True)
class _MandateLoadResult:
    mandate: ManageMandateSource | None
    failure_reason: str | None = None


@dataclass(frozen=True)
class _HealthLoadResult:
    health: ManageMandateHealthSource | None
    failure_reason: str | None = None


@dataclass(frozen=True)
class _CashLoadResult:
    cash: WorkbenchCashMeasureSource | None
    failure_reason: str | None = None


async def load_risk_mandate_sources(
    *,
    manage_client: RiskMandateManageClient,
    cash_source: RiskMandateCashSource,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
) -> RiskMandateSources:
    mandate_result, cash_result = await asyncio.gather(
        _load_mandate(
            manage_client=manage_client,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        ),
        _load_cash(
            cash_source=cash_source,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        ),
    )
    health_result = (
        await _load_health(
            manage_client=manage_client,
            mandate_id=mandate_result.mandate.mandate_id,
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
        )
        if mandate_result.mandate is not None
        else _HealthLoadResult(
            health=None,
            failure_reason="Mandate health cannot be resolved without an approved mandate.",
        )
    )
    return RiskMandateSources(
        mandate=mandate_result.mandate,
        health=health_result.health,
        cash=cash_result.cash,
        mandate_failure_reason=mandate_result.failure_reason,
        health_failure_reason=health_result.failure_reason,
        cash_failure_reason=cash_result.failure_reason,
    )


async def _load_mandate(
    *,
    manage_client: RiskMandateManageClient,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
) -> _MandateLoadResult:
    upstream_status, upstream_payload = await manage_client.get_mandate_by_portfolio(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        as_of_date=as_of_date,
    )
    if upstream_status >= status.HTTP_400_BAD_REQUEST:
        return _MandateLoadResult(
            mandate=None,
            failure_reason="The approved client mandate is unavailable from Lotus Manage.",
        )
    try:
        mandate = ManageMandateSource.model_validate(upstream_payload)
    except ValidationError:
        return _MandateLoadResult(
            mandate=None,
            failure_reason="Lotus Manage returned incomplete mandate evidence.",
        )
    if mandate.portfolio_id != portfolio_id:
        return _MandateLoadResult(
            mandate=None,
            failure_reason="Lotus Manage returned mandate evidence for a different portfolio.",
        )
    return _MandateLoadResult(mandate=mandate)


async def _load_health(
    *,
    manage_client: RiskMandateManageClient,
    mandate_id: str,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
) -> _HealthLoadResult:
    upstream_status, upstream_payload = await manage_client.get_mandate_health(
        mandate_id=mandate_id,
        correlation_id=correlation_id,
        as_of_date=as_of_date,
    )
    if upstream_status >= status.HTTP_400_BAD_REQUEST:
        return _HealthLoadResult(
            health=None,
            failure_reason="Mandate-health evidence is unavailable from Lotus Manage.",
        )
    try:
        health = ManageMandateHealthSource.model_validate(upstream_payload)
    except ValidationError:
        return _HealthLoadResult(
            health=None,
            failure_reason="Lotus Manage returned incomplete mandate-health evidence.",
        )
    if health.mandate_id != mandate_id or health.portfolio_id != portfolio_id:
        return _HealthLoadResult(
            health=None,
            failure_reason=(
                "Lotus Manage returned health evidence for a different mandate or portfolio."
            ),
        )
    return _HealthLoadResult(health=health)


async def _load_cash(
    *,
    cash_source: RiskMandateCashSource,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str,
) -> _CashLoadResult:
    try:
        overview = await cash_source.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            include_performance_snapshot=False,
            include_rebalance_snapshot=False,
            requested_as_of_date=as_of_date,
        )
    except HTTPException:
        return _CashLoadResult(
            cash=None,
            failure_reason="Cash allocation is unavailable for the selected review date.",
        )
    effective_as_of = overview.effective_as_of_date or overview.as_of_date
    cash_weight_pct = overview.overview.cash_weight_pct
    if overview.as_of_state == "unavailable" or effective_as_of is None:
        return _CashLoadResult(
            cash=None,
            failure_reason="Cash allocation has no usable business-date evidence.",
        )
    if cash_weight_pct < 0 or cash_weight_pct > 100:
        return _CashLoadResult(
            cash=None,
            failure_reason="Cash allocation is outside the supported percentage range.",
        )
    try:
        source_as_of_date = date.fromisoformat(effective_as_of)
    except ValueError:
        return _CashLoadResult(
            cash=None,
            failure_reason="Cash allocation has invalid business-date evidence.",
        )
    return _CashLoadResult(
        cash=WorkbenchCashMeasureSource(
            value=cash_weight_pct / 100,
            as_of_date=source_as_of_date,
        )
    )
