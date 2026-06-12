from app.services.portfolio_transaction_ledger import (
    PortfolioTransactionsRequestContext,
    build_transaction_ledger_response,
    parse_transaction_views,
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
