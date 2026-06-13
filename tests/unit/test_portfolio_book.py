from app.contracts.portfolio_core import PortfolioSummary
from app.contracts.portfolio_holdings import (
    PortfolioAllocationBucket,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioTopPosition,
)
from app.services.portfolio_book import build_portfolio_book_response


def test_build_portfolio_book_response_combines_source_payloads() -> None:
    positions = [
        PortfolioPositionView(
            security_id="EQ_1",
            instrument_name="Example Equity",
            quantity=10.0,
            market_value_base=900.0,
        )
    ]
    response = build_portfolio_book_response(
        correlation_id="corr-book",
        contract_version="v-test",
        as_of_date="2026-03-31",
        portfolio_payload={
            "portfolio_id": "PF_1001",
            "base_currency": "USD",
            "client_id": "CIF_1",
            "status": "ACTIVE",
        },
        cash_balances_payload={
            "cash_accounts": [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "account_currency": "USD",
                    "balance_account_currency": "100.555",
                    "balance_reporting_currency": "100.555",
                }
            ]
        },
        allocations=PortfolioAllocationResponse(
            correlation_id="corr-book",
            contract_version="v-test",
            portfolio_id="PF_1001",
            as_of_date="2026-03-31",
            summary=PortfolioSummary(
                assets_under_management_base=1000.0,
                invested_market_value_base=900.0,
                cash_market_value_base=100.0,
                cash_weight_pct=10.0,
                position_count=2,
                cash_balance_count=1,
            ),
            views=[
                PortfolioAllocationView(
                    dimension="asset_class",
                    buckets=[
                        PortfolioAllocationBucket(
                            bucket="Equity",
                            position_count=1,
                            market_value_base=900.0,
                            weight_pct=90.0,
                        )
                    ],
                )
            ],
        ),
        positions=PortfolioPositionBookResponse(
            correlation_id="corr-book",
            contract_version="v-test",
            portfolio_id="PF_1001",
            as_of_date="2026-03-31",
            summary=PortfolioSummary(
                assets_under_management_base=1000.0,
                invested_market_value_base=900.0,
                cash_market_value_base=100.0,
                cash_weight_pct=10.0,
                position_count=2,
                cash_balance_count=1,
            ),
            top_positions=[PortfolioTopPosition(**positions[0].model_dump())],
            positions=positions,
        ),
    )

    assert response.correlation_id == "corr-book"
    assert response.contract_version == "v-test"
    assert response.as_of_date == "2026-03-31"
    assert response.portfolio.portfolio_id == "PF_1001"
    assert response.summary.assets_under_management_base == 1000.0
    assert response.cash_balances[0].market_value_base == 100.56
    assert response.cash_balances[0].weight_pct == 10.056
    assert response.allocation_views[0].dimension == "asset_class"
    assert response.top_positions[0].security_id == "EQ_1"
    assert response.positions[0].security_id == "EQ_1"
