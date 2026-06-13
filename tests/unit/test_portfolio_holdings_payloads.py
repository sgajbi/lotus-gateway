from app.services.portfolio_holdings_payloads import parse_allocation_views, parse_cash_balances


def test_parse_allocation_views_quantizes_buckets_and_ignores_non_mapping_rows() -> None:
    views = parse_allocation_views(
        {
            "views": [
                "ignored",
                {
                    "dimension": "asset_class",
                    "buckets": [
                        {
                            "dimension_value": "Equity",
                            "position_count": 3,
                            "market_value_reporting_currency": "1234.567",
                            "weight": "0.345678",
                        },
                        "ignored",
                    ],
                },
            ]
        }
    )

    assert len(views) == 1
    assert views[0].dimension == "asset_class"
    assert len(views[0].buckets) == 1
    bucket = views[0].buckets[0]
    assert bucket.bucket == "Equity"
    assert bucket.position_count == 3
    assert bucket.market_value_base == 1234.57
    assert bucket.weight_pct == 34.5678


def test_parse_cash_balances_quantizes_values_and_weight() -> None:
    balances = parse_cash_balances(
        {
            "cash_accounts": [
                {
                    "security_id": "CASH_USD",
                    "instrument_name": "USD Cash",
                    "account_currency": " USD ",
                    "balance_account_currency": "100.555",
                    "balance_reporting_currency": "100.555",
                }
            ]
        },
        total_aum=1000.0,
    )

    assert len(balances) == 1
    balance = balances[0]
    assert balance.security_id == "CASH_USD"
    assert balance.instrument_name == "USD Cash"
    assert balance.currency == "USD"
    assert balance.quantity == 100.56
    assert balance.market_value_base == 100.56
    assert balance.weight_pct == 10.056


def test_parse_cash_balances_uses_zero_weight_when_total_aum_is_zero() -> None:
    balances = parse_cash_balances(
        {
            "cash_accounts": [
                {
                    "security_id": "CASH_SGD",
                    "instrument_name": "SGD Cash",
                    "account_currency": "   ",
                    "balance_account_currency": 50,
                    "balance_reporting_currency": 50,
                }
            ]
        },
        total_aum=0.0,
    )

    assert balances[0].currency is None
    assert balances[0].weight_pct == 0.0
