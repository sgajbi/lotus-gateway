from app.contracts import portfolio
from app.contracts.portfolio_core import PortfolioIdentity, PortfolioSummary
from app.contracts.portfolio_holdings import (
    PortfolioAllocationBucket,
    PortfolioAllocationResponse,
    PortfolioAllocationView,
    PortfolioBookResponse,
    PortfolioCashBalance,
    PortfolioPositionBookResponse,
    PortfolioPositionView,
    PortfolioTopPosition,
)
from app.contracts.portfolio_position_book import (
    PortfolioPositionBookResponse as ExtractedPortfolioPositionBookResponse,
)
from app.contracts.portfolio_position_book import (
    PortfolioPositionView as ExtractedPortfolioPositionView,
)
from app.contracts.portfolio_position_book import (
    PortfolioTopPosition as ExtractedPortfolioTopPosition,
)


def test_portfolio_core_contracts_remain_compatibility_reexports() -> None:
    assert portfolio.PortfolioIdentity is PortfolioIdentity
    assert portfolio.PortfolioSummary is PortfolioSummary


def test_portfolio_holdings_contracts_remain_compatibility_reexports() -> None:
    assert portfolio.PortfolioAllocationBucket is PortfolioAllocationBucket
    assert portfolio.PortfolioAllocationResponse is PortfolioAllocationResponse
    assert portfolio.PortfolioAllocationView is PortfolioAllocationView
    assert portfolio.PortfolioBookResponse is PortfolioBookResponse
    assert portfolio.PortfolioCashBalance is PortfolioCashBalance
    assert portfolio.PortfolioPositionBookResponse is PortfolioPositionBookResponse
    assert portfolio.PortfolioPositionView is PortfolioPositionView
    assert portfolio.PortfolioTopPosition is PortfolioTopPosition
    assert PortfolioPositionBookResponse is ExtractedPortfolioPositionBookResponse
    assert PortfolioPositionView is ExtractedPortfolioPositionView
    assert PortfolioTopPosition is ExtractedPortfolioTopPosition


def test_portfolio_book_contract_accepts_extracted_core_and_holdings_models() -> None:
    summary = PortfolioSummary(
        assets_under_management_base=1000.0,
        invested_market_value_base=900.0,
        cash_market_value_base=100.0,
        cash_weight_pct=10.0,
        position_count=1,
        cash_balance_count=1,
    )

    response = PortfolioBookResponse(
        correlation_id="corr-book",
        as_of_date="2026-03-27",
        portfolio=PortfolioIdentity(
            portfolio_id="PF_1001",
            display_name="PF_1001",
            client_id="CIF_1",
            base_currency="USD",
            booking_center_code="SGPB",
        ),
        summary=summary,
        cash_balances=[
            PortfolioCashBalance(
                security_id="CASH_USD",
                instrument_name="USD Cash",
                currency="USD",
                quantity=100.0,
                market_value_base=100.0,
                weight_pct=10.0,
            )
        ],
        allocation_views=[
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
        top_positions=[
            PortfolioTopPosition(
                security_id="EQ_1",
                instrument_name="Equity 1",
                asset_class="Equity",
                quantity=10.0,
                market_value_base=900.0,
                weight_pct=90.0,
            )
        ],
        positions=[
            PortfolioPositionView(
                security_id="EQ_1",
                instrument_name="Equity 1",
                asset_class="Equity",
                quantity=10.0,
                market_value_base=900.0,
                weight_pct=90.0,
            )
        ],
    )

    assert response.summary is summary
    assert response.model_dump()["portfolio"]["portfolio_id"] == "PF_1001"


def test_portfolio_position_book_contract_uses_extracted_holdings_models() -> None:
    response = PortfolioPositionBookResponse(
        correlation_id="corr-positions",
        portfolio_id="PF_1001",
        as_of_date="2026-03-27",
        summary=PortfolioSummary(
            assets_under_management_base=1000.0,
            invested_market_value_base=900.0,
            cash_market_value_base=100.0,
            cash_weight_pct=10.0,
            position_count=1,
            cash_balance_count=1,
        ),
        positions=[
            PortfolioPositionView(
                security_id="EQ_1",
                instrument_name="Equity 1",
                quantity=10.0,
            )
        ],
    )

    assert response.contract_version == "v1"
    assert response.positions[0].security_id == "EQ_1"
