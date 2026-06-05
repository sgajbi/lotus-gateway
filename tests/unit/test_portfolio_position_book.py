from app.services.portfolio_position_book import (
    build_top_positions,
    parse_position_book_summary,
    parse_positions,
)


def test_parse_position_book_summary_uses_cash_positions_without_cash_endpoint():
    summary = parse_position_book_summary(
        {
            "portfolios": [
                {
                    "aum_reporting_currency": 1000,
                    "position_count": 3,
                }
            ]
        },
        {
            "positions": [
                {
                    "asset_class": "Cash",
                    "valuation": {"market_value_base": 125.50},
                },
                {
                    "asset_class": "Equity",
                    "valuation": {"market_value_base": 874.50},
                },
            ]
        },
    )

    assert summary.assets_under_management_base == 1000.0
    assert summary.invested_market_value_base == 874.5
    assert summary.cash_market_value_base == 125.5
    assert summary.cash_weight_pct == 12.55
    assert summary.position_count == 3
    assert summary.cash_balance_count == 1


def test_parse_positions_preserves_legacy_valuation_fallbacks():
    positions = parse_positions(
        {
            "positions": [
                "ignored",
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Example Equity",
                    "asset_class": "Equity",
                    "isin": "US1234567890",
                    "currency": "USD",
                    "sector": "Technology",
                    "country_of_risk": "United States",
                    "held_since_date": "2025-12-31",
                    "quantity": 10,
                    "cost_basis": 500,
                    "cost_basis_local": 500,
                    "weight": 0.07,
                    "valuation": {
                        "market_price": 70,
                        "market_value": 700,
                        "unrealized_gain_loss": 200,
                    },
                    "reprocessing_status": "READY",
                },
            ]
        }
    )

    assert len(positions) == 1
    position = positions[0]
    assert position.security_id == "EQ_1"
    assert position.market_price == 70.0
    assert position.market_value_base == 700.0
    assert position.market_value_local == 700.0
    assert position.unrealized_gain_loss_base == 200.0
    assert position.unrealized_gain_loss_local == 200.0
    assert position.weight_pct == 7.0
    assert position.reprocessing_status == "READY"


def test_build_top_positions_ranks_by_market_value_and_limits_to_ten():
    positions = parse_positions(
        {
            "positions": [
                {
                    "security_id": f"EQ_{index}",
                    "instrument_name": f"Equity {index}",
                    "quantity": 1,
                    "valuation": {"market_value_base": index * 10},
                }
                for index in range(12)
            ]
        }
    )

    top_positions = build_top_positions(positions)

    assert len(top_positions) == 10
    assert top_positions[0].security_id == "EQ_11"
    assert top_positions[-1].security_id == "EQ_2"
