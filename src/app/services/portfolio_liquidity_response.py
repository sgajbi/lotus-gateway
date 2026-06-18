from typing import Any

from app.contracts.portfolio_common import PortfolioPartialFailure
from app.contracts.portfolio_liquidity import (
    PortfolioLiquidityResponse,
    PortfolioProjectedCashflowResponse,
)
from app.services.portfolio_holdings_payloads import parse_cash_balances
from app.services.portfolio_liquidity_payloads import PortfolioLiquidityPayloads
from app.services.portfolio_workspace_components import (
    extract_resolved_as_of_date,
    parse_cashflow,
    parse_summary,
)

UpstreamResult = tuple[int, dict[str, Any]]


def build_portfolio_liquidity_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    as_of_date: str | None,
    default_as_of_date: str,
    payloads: PortfolioLiquidityPayloads,
) -> PortfolioLiquidityResponse:
    warnings: list[str] = []
    partial_failures: list[PortfolioPartialFailure] = []
    summary = parse_summary(
        payloads.aum_result,
        payloads.cash_balances_result,
        warnings,
        partial_failures,
    )
    return PortfolioLiquidityResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        as_of_date=str(
            payloads.aum_payload.get("resolved_as_of_date") or as_of_date or default_as_of_date
        ),
        portfolio_id=portfolio_id,
        summary=summary,
        cash_balances=parse_cash_balances(
            payloads.cash_balances_payload,
            summary.assets_under_management_base,
        ),
        cashflow_outlook=parse_cashflow(
            payloads.cashflow_result,
            warnings,
            partial_failures,
        ),
        warnings=warnings,
        partial_failures=partial_failures,
    )


def build_projected_cashflow_response(
    *,
    correlation_id: str,
    contract_version: str,
    portfolio_id: str,
    as_of_date: str | None,
    default_as_of_date: str,
    cashflow_result: UpstreamResult,
) -> PortfolioProjectedCashflowResponse:
    warnings: list[str] = []
    partial_failures: list[PortfolioPartialFailure] = []
    cashflow_outlook = parse_cashflow(cashflow_result, warnings, partial_failures)
    resolved_as_of_date = extract_resolved_as_of_date(cashflow_result)

    return PortfolioProjectedCashflowResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        as_of_date=resolved_as_of_date or as_of_date or default_as_of_date,
        cashflow_outlook=cashflow_outlook,
        warnings=warnings,
        partial_failures=partial_failures,
    )
