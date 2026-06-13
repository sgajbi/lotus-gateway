import pytest

from app.services.portfolio_holdings_payloads import (
    ALLOCATION_VIEW_DIMENSIONS,
    PortfolioAllocationLoadRequest,
    PortfolioAllocationPayloadLoaders,
    PortfolioPositionBookLoadRequest,
    PortfolioPositionBookPayloadLoaders,
    build_portfolio_allocation_response,
    load_portfolio_allocation_payloads,
    load_portfolio_position_book_payloads,
    parse_allocation_views,
    parse_cash_balances,
    parse_look_through_capability,
)


@pytest.mark.asyncio
async def test_load_portfolio_allocation_payloads_queries_sources_and_requires_payloads() -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    aum_result = (200, {"portfolios": [{"aum_reporting_currency": "1000"}]})
    positions_result = (200, {"positions": [{"security_id": "EQ_1"}]})
    allocation_result = (200, {"views": []})

    async def query_aum_result(**kwargs):
        calls.append(("aum", kwargs))
        return aum_result

    async def get_portfolio_positions_result(**kwargs):
        calls.append(("positions", kwargs))
        return positions_result

    async def query_asset_allocation_result(**kwargs):
        calls.append(("allocation", kwargs))
        return allocation_result

    required: list[tuple[object, str]] = []

    def require_payload(*, result, unavailable_detail_prefix: str):
        required.append((result, unavailable_detail_prefix))
        return result[1]

    payloads = await load_portfolio_allocation_payloads(
        PortfolioAllocationLoadRequest(
            portfolio_id="PF_1001",
            correlation_id="corr-allocation",
            as_of_date="2026-03-31",
            reporting_currency="USD",
            look_through_mode="full",
        ),
        PortfolioAllocationPayloadLoaders(
            query_aum_result=query_aum_result,
            get_portfolio_positions_result=get_portfolio_positions_result,
            query_asset_allocation_result=query_asset_allocation_result,
            require_payload=require_payload,
        ),
    )

    assert payloads.aum_result == aum_result
    assert payloads.aum_payload == aum_result[1]
    assert payloads.positions_payload == positions_result[1]
    assert payloads.allocation_payload == allocation_result[1]
    assert (
        "aum",
        {
            "correlation_id": "corr-allocation",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-31",
            "reporting_currency": "USD",
        },
    ) in calls
    assert (
        "positions",
        {
            "portfolio_id": "PF_1001",
            "correlation_id": "corr-allocation",
            "as_of_date": "2026-03-31",
            "include_projected": False,
            "reporting_currency": "USD",
        },
    ) in calls
    assert (
        "allocation",
        {
            "correlation_id": "corr-allocation",
            "portfolio_id": "PF_1001",
            "as_of_date": "2026-03-31",
            "dimensions": ALLOCATION_VIEW_DIMENSIONS,
            "reporting_currency": "USD",
            "look_through_mode": "full",
        },
    ) in calls
    assert required == [
        (aum_result, "lotus-core aum unavailable"),
        (allocation_result, "lotus-core allocation unavailable"),
        (positions_result, "lotus-core positions unavailable"),
    ]


@pytest.mark.asyncio
async def test_load_portfolio_position_book_payloads_queries_sources_and_requires_payloads() -> (
    None
):
    calls: list[tuple[str, dict[str, object]]] = []
    aum_result = (200, {"portfolios": [{"aum_reporting_currency": "1250"}]})
    positions_result = (200, {"positions": [{"security_id": "FI_1"}]})

    async def query_aum_result(**kwargs):
        calls.append(("aum", kwargs))
        return aum_result

    async def get_portfolio_positions_result(**kwargs):
        calls.append(("positions", kwargs))
        return positions_result

    required: list[tuple[object, str]] = []

    def require_payload(*, result, unavailable_detail_prefix: str):
        required.append((result, unavailable_detail_prefix))
        return result[1]

    payloads = await load_portfolio_position_book_payloads(
        PortfolioPositionBookLoadRequest(
            portfolio_id="PF_2002",
            correlation_id="corr-positions",
            as_of_date="2026-04-30",
            include_projected=True,
            reporting_currency="CHF",
        ),
        PortfolioPositionBookPayloadLoaders(
            query_aum_result=query_aum_result,
            get_portfolio_positions_result=get_portfolio_positions_result,
            require_payload=require_payload,
        ),
    )

    assert payloads.aum_payload == aum_result[1]
    assert payloads.positions_payload == positions_result[1]
    assert (
        "aum",
        {
            "correlation_id": "corr-positions",
            "portfolio_id": "PF_2002",
            "as_of_date": "2026-04-30",
            "reporting_currency": "CHF",
        },
    ) in calls
    assert (
        "positions",
        {
            "portfolio_id": "PF_2002",
            "correlation_id": "corr-positions",
            "as_of_date": "2026-04-30",
            "include_projected": True,
            "reporting_currency": "CHF",
        },
    ) in calls
    assert required == [
        (aum_result, "lotus-core aum unavailable"),
        (positions_result, "lotus-core positions unavailable"),
    ]


def test_build_portfolio_allocation_response_preserves_summary_views_and_look_through() -> None:
    response = build_portfolio_allocation_response(
        correlation_id="corr-allocation",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date=None,
        default_as_of_date="2026-03-27",
        reporting_currency="USD",
        aum_payload={
            "resolved_as_of_date": "2026-03-26",
            "portfolios": [
                {
                    "aum_reporting_currency": "1000",
                    "position_count": 2,
                }
            ],
        },
        positions_payload={
            "positions": [
                {"instrument_type": "EQUITY"},
                {
                    "asset_class": "CASH",
                    "valuation": {"market_value_base": "100"},
                },
            ]
        },
        allocation_payload={
            "reporting_currency": " SGD ",
            "look_through": {
                "requested_mode": "full",
                "effective_mode": "direct_only",
                "applied": False,
            },
            "views": [
                {
                    "dimension": "region",
                    "buckets": [
                        {
                            "dimension_value": "Asia",
                            "position_count": 2,
                            "market_value_reporting_currency": "700.123",
                            "weight": "0.7",
                        }
                    ],
                }
            ],
        },
    )

    assert response.correlation_id == "corr-allocation"
    assert response.portfolio_id == "PF_1001"
    assert response.as_of_date == "2026-03-26"
    assert response.reporting_currency == "SGD"
    assert response.look_through is not None
    assert response.look_through.requested_mode == "full"
    assert response.look_through.effective_mode == "direct_only"
    assert response.look_through.applied is False
    assert response.summary.assets_under_management_base == 1000.0
    assert response.summary.cash_market_value_base == 100.0
    assert response.summary.cash_weight_pct == 10.0
    assert response.views[0].dimension == "region"
    assert response.views[0].buckets[0].market_value_base == 700.12


def test_build_portfolio_allocation_response_uses_request_currency_and_default_date() -> None:
    response = build_portfolio_allocation_response(
        correlation_id="corr-allocation-fallback",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date=None,
        default_as_of_date="2026-03-27",
        reporting_currency="USD",
        aum_payload={
            "assets_under_management_base": "0",
            "cash_market_value_base": "0",
        },
        positions_payload={"positions": []},
        allocation_payload={"reporting_currency": " "},
    )

    assert response.as_of_date == "2026-03-27"
    assert response.reporting_currency == "USD"
    assert response.look_through is None
    assert response.views == []


def test_parse_look_through_capability_rejects_incomplete_payloads() -> None:
    assert parse_look_through_capability(None) is None
    assert parse_look_through_capability({"requested_mode": "full"}) is None


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
