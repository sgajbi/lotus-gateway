from app.services.portfolio_liquidity_payloads import PortfolioLiquidityPayloads
from app.services.portfolio_liquidity_response import (
    build_portfolio_liquidity_response,
    build_projected_cashflow_response,
)


def test_build_portfolio_liquidity_response_assembles_cash_and_cashflow() -> None:
    payloads = PortfolioLiquidityPayloads(
        aum_result=(
            200,
            {
                "resolved_as_of_date": "2026-03-27",
                "portfolios": [
                    {
                        "aum_reporting_currency": 1000,
                        "position_count": 3,
                    }
                ],
            },
        ),
        cash_balances_result=(
            200,
            {
                "totals": {
                    "total_balance_reporting_currency": 100,
                    "cash_account_count": 1,
                },
                "cash_accounts": [
                    {
                        "security_id": "CASH_USD",
                        "instrument_name": "USD Cash",
                        "account_currency": "USD",
                        "balance_account_currency": 100,
                        "balance_reporting_currency": 100,
                    }
                ],
            },
        ),
        cashflow_result=(
            200,
            {
                "as_of_date": "2026-03-27",
                "range_end_date": "2026-04-06",
                "total_net_cashflow": -25,
                "projection_days": 10,
                "include_projected": True,
                "points": [
                    {
                        "projection_date": "2026-03-28",
                        "net_cashflow": -25,
                        "projected_cumulative_cashflow": -25,
                    }
                ],
            },
        ),
        aum_payload={
            "resolved_as_of_date": "2026-03-27",
            "portfolios": [{"aum_reporting_currency": 1000, "position_count": 3}],
        },
        cash_balances_payload={
            "totals": {"total_balance_reporting_currency": 100, "cash_account_count": 1},
            "cash_accounts": [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "account_currency": "USD",
                    "balance_account_currency": 100,
                    "balance_reporting_currency": 100,
                }
            ],
        },
    )

    response = build_portfolio_liquidity_response(
        correlation_id="corr-liquidity",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date=None,
        default_as_of_date="2026-03-26",
        payloads=payloads,
    )

    assert response.as_of_date == "2026-03-27"
    assert response.summary.cash_weight_pct == 10.0
    assert response.cash_balances[0].weight_pct == 10.0
    assert response.cashflow_outlook is not None
    assert response.cashflow_outlook.total_net_cashflow_base == -25.0
    assert response.warnings == []
    assert response.partial_failures == []


def test_build_projected_cashflow_response_preserves_degraded_source_failure() -> None:
    response = build_projected_cashflow_response(
        correlation_id="corr-projected",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        default_as_of_date="2026-03-26",
        cashflow_result=(503, {"detail": "cashflow temporarily unavailable"}),
    )

    assert response.as_of_date == "2026-03-27"
    assert response.cashflow_outlook is None
    assert response.warnings == ["PORTFOLIO_CASHFLOW_UNAVAILABLE"]
    assert response.partial_failures[0].source_service == "lotus-core"
    assert response.partial_failures[0].error_code == "PORTFOLIO_CASHFLOW_UNAVAILABLE"
    assert response.partial_failures[0].detail == "cashflow temporarily unavailable"
