from app.services.portfolio_transaction_ledger import (
    PortfolioTransactionsRequestContext,
    build_portfolio_transactions_request_context,
    build_transaction_ledger_response,
    build_transaction_rows_page_request_context,
    parse_transaction_views,
    portfolio_transactions_cache_key,
    portfolio_transactions_client_kwargs,
)


def _request_context() -> PortfolioTransactionsRequestContext:
    return PortfolioTransactionsRequestContext(
        portfolio_id="PF_1001",
        correlation_id="corr-ledger",
        as_of_date="2026-03-27",
        include_projected=True,
        skip=20,
        limit=25,
        transaction_type=None,
        security_id=None,
        instrument_id=None,
        component_type=None,
        linked_transaction_group_id=None,
        fx_contract_id=None,
        swap_event_id=None,
        near_leg_group_id=None,
        far_leg_group_id=None,
        sort_by="transaction_date",
        sort_order="desc",
        start_date=None,
        end_date=None,
        reporting_currency="USD",
    )


def test_build_transaction_ledger_response_preserves_source_metadata():
    response = build_transaction_ledger_response(
        context=_request_context(),
        contract_version="v-test",
        result_payload={
            "as_of_date": "2026-03-28",
            "total": 30,
            "skip": 20,
            "limit": 10,
            "transactions": [],
        },
    )

    assert response.correlation_id == "corr-ledger"
    assert response.contract_version == "v-test"
    assert response.portfolio_id == "PF_1001"
    assert response.as_of_date == "2026-03-28"
    assert response.include_projected is True
    assert response.total == 30
    assert response.skip == 20
    assert response.limit == 10


def test_build_portfolio_transactions_request_context_preserves_filters():
    context = build_portfolio_transactions_request_context(
        portfolio_id="PF_1001",
        correlation_id="corr-ledger",
        as_of_date="2026-03-27",
        include_projected=False,
        skip=10,
        limit=50,
        transaction_type="FX_FORWARD",
        security_id="SEC_1",
        instrument_id="INST_1",
        component_type="FX_CONTRACT_OPEN",
        linked_transaction_group_id="LTG-FX-2026-0001",
        fx_contract_id="FXC-2026-0001",
        swap_event_id="FXSWAP-2026-0001",
        near_leg_group_id="FXSWAP-2026-0001-NEAR",
        far_leg_group_id="FXSWAP-2026-0001-FAR",
        sort_by="settlement_date",
        sort_order="asc",
        start_date="2026-01-01",
        end_date="2026-03-31",
        reporting_currency="CHF",
    )

    assert context.portfolio_id == "PF_1001"
    assert context.correlation_id == "corr-ledger"
    assert context.include_projected is False
    assert context.skip == 10
    assert context.limit == 50
    assert context.transaction_type == "FX_FORWARD"
    assert context.security_id == "SEC_1"
    assert context.instrument_id == "INST_1"
    assert context.component_type == "FX_CONTRACT_OPEN"
    assert context.linked_transaction_group_id == "LTG-FX-2026-0001"
    assert context.fx_contract_id == "FXC-2026-0001"
    assert context.swap_event_id == "FXSWAP-2026-0001"
    assert context.near_leg_group_id == "FXSWAP-2026-0001-NEAR"
    assert context.far_leg_group_id == "FXSWAP-2026-0001-FAR"
    assert context.sort_by == "settlement_date"
    assert context.sort_order == "asc"
    assert context.start_date == "2026-01-01"
    assert context.end_date == "2026-03-31"
    assert context.reporting_currency == "CHF"


def test_portfolio_transactions_cache_key_includes_all_request_filters():
    context = build_portfolio_transactions_request_context(
        portfolio_id="PF_1001",
        correlation_id="corr-ledger",
        as_of_date="2026-03-27",
        include_projected=True,
        skip=20,
        limit=25,
        transaction_type="DIVIDEND",
        security_id="SEC_1",
        instrument_id="INST_1",
        component_type="CASH_DIVIDEND",
        linked_transaction_group_id="LTG-1",
        fx_contract_id="FXC-1",
        swap_event_id="SWAP-1",
        near_leg_group_id="NEAR-1",
        far_leg_group_id="FAR-1",
        sort_by="transaction_date",
        sort_order="desc",
        start_date="2026-01-01",
        end_date="2026-03-31",
        reporting_currency="USD",
    )

    assert portfolio_transactions_cache_key(context) == (
        "transactions",
        "PF_1001",
        "2026-03-27",
        True,
        20,
        25,
        "DIVIDEND",
        "SEC_1",
        "INST_1",
        "CASH_DIVIDEND",
        "LTG-1",
        "FXC-1",
        "SWAP-1",
        "NEAR-1",
        "FAR-1",
        "transaction_date",
        "desc",
        "2026-01-01",
        "2026-03-31",
        "USD",
    )


def test_portfolio_transactions_client_kwargs_include_all_request_filters():
    context = build_portfolio_transactions_request_context(
        portfolio_id="PF_1001",
        correlation_id="corr-ledger",
        as_of_date="2026-03-27",
        include_projected=True,
        skip=20,
        limit=25,
        transaction_type="DIVIDEND",
        security_id="SEC_1",
        instrument_id="INST_1",
        component_type="CASH_DIVIDEND",
        linked_transaction_group_id="LTG-1",
        fx_contract_id="FXC-1",
        swap_event_id="SWAP-1",
        near_leg_group_id="NEAR-1",
        far_leg_group_id="FAR-1",
        sort_by="transaction_date",
        sort_order="desc",
        start_date="2026-01-01",
        end_date="2026-03-31",
        reporting_currency="USD",
    )

    assert portfolio_transactions_client_kwargs(context) == {
        "portfolio_id": "PF_1001",
        "correlation_id": "corr-ledger",
        "as_of_date": "2026-03-27",
        "include_projected": True,
        "skip": 20,
        "limit": 25,
        "sort_by": "transaction_date",
        "sort_order": "desc",
        "transaction_type": "DIVIDEND",
        "security_id": "SEC_1",
        "instrument_id": "INST_1",
        "component_type": "CASH_DIVIDEND",
        "linked_transaction_group_id": "LTG-1",
        "fx_contract_id": "FXC-1",
        "swap_event_id": "SWAP-1",
        "near_leg_group_id": "NEAR-1",
        "far_leg_group_id": "FAR-1",
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "reporting_currency": "USD",
    }


def test_build_transaction_rows_page_request_context_uses_summary_page_defaults():
    context = build_transaction_rows_page_request_context(
        portfolio_id="PF_1001",
        correlation_id="corr-summary-page",
        as_of_date="2026-03-27",
        skip=100,
        limit=50,
        start_date="2026-01-01",
        end_date="2026-03-31",
        reporting_currency="CHF",
    )

    assert context.portfolio_id == "PF_1001"
    assert context.correlation_id == "corr-summary-page"
    assert context.as_of_date == "2026-03-27"
    assert context.include_projected is False
    assert context.skip == 100
    assert context.limit == 50
    assert context.sort_by == "transaction_date"
    assert context.sort_order == "asc"
    assert context.start_date == "2026-01-01"
    assert context.end_date == "2026-03-31"
    assert context.reporting_currency == "CHF"
    assert context.transaction_type is None
    assert context.security_id is None
    assert context.instrument_id is None
    assert context.component_type is None
    assert context.linked_transaction_group_id is None
    assert context.fx_contract_id is None
    assert context.swap_event_id is None
    assert context.near_leg_group_id is None
    assert context.far_leg_group_id is None


def test_build_transaction_ledger_response_falls_back_to_context_metadata():
    response = build_transaction_ledger_response(
        context=_request_context(),
        contract_version="v-test",
        result_payload={"transactions": []},
    )

    assert response.as_of_date == "2026-03-27"
    assert response.total == 0
    assert response.skip == 20
    assert response.limit == 25


def test_parse_transaction_views_quantizes_amounts_and_preserves_event_identifiers():
    transactions = parse_transaction_views(
        {
            "transactions": [
                "ignored",
                {
                    "transaction_id": "TX_1",
                    "transaction_date": "2026-03-27T09:30:00Z",
                    "settlement_date": "2026-03-29",
                    "transaction_type": "FX_FORWARD",
                    "component_type": "FX_CONTRACT_OPEN",
                    "security_id": "EQ_1",
                    "instrument_id": "INST_EQ_1",
                    "quantity": "10.1234567",
                    "price": "70.123456",
                    "gross_transaction_amount": "700.129",
                    "currency": "USD",
                    "net_cost": "700.129",
                    "realized_gain_loss": "15.129",
                    "settlement_status": "SETTLED",
                    "source_system": "lotus-core",
                    "cash_entry_mode": "BOOKED",
                    "economic_event_id": "EVT-2026-0001",
                    "linked_transaction_group_id": "LTG-FX-2026-0001",
                    "fx_contract_id": "FXC-2026-0001",
                    "swap_event_id": "FXSWAP-2026-0001",
                    "near_leg_group_id": "FXSWAP-2026-0001-NEAR",
                    "far_leg_group_id": "FXSWAP-2026-0001-FAR",
                },
            ]
        }
    )

    assert len(transactions) == 1
    transaction = transactions[0]
    assert transaction.transaction_id == "TX_1"
    assert transaction.quantity == 10.123457
    assert transaction.price == 70.123456
    assert transaction.gross_amount == 700.13
    assert transaction.net_cost_base == 700.13
    assert transaction.realized_gain_loss_base == 15.13
    assert transaction.component_type == "FX_CONTRACT_OPEN"
    assert transaction.linked_transaction_group_id == "LTG-FX-2026-0001"
    assert transaction.fx_contract_id == "FXC-2026-0001"
    assert transaction.swap_event_id == "FXSWAP-2026-0001"
    assert transaction.near_leg_group_id == "FXSWAP-2026-0001-NEAR"
    assert transaction.far_leg_group_id == "FXSWAP-2026-0001-FAR"


def test_parse_transaction_views_preserves_missing_optional_amounts():
    transaction = parse_transaction_views(
        {
            "transactions": [
                {
                    "transaction_id": "TX_2",
                    "transaction_date": "2026-03-27",
                    "transaction_type": "DIVIDEND",
                    "security_id": "EQ_1",
                    "instrument_id": "INST_EQ_1",
                }
            ]
        }
    )[0]

    assert transaction.price is None
    assert transaction.gross_amount is None
    assert transaction.net_cost_base is None
    assert transaction.realized_gain_loss_base is None
