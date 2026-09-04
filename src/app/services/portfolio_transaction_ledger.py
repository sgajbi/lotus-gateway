from typing import Any

from fastapi import HTTPException, status

from app.contracts.portfolio_transactions import (
    PortfolioTransactionLedgerResponse,
    PortfolioTransactionRecordResponse,
    PortfolioTransactionView,
)
from app.precision_policy import quantize_money, quantize_price, quantize_quantity
from app.services.portfolio_transaction_requests import PortfolioTransactionsRequestContext
from app.services.portfolio_transaction_temporal import parse_transaction_timestamp
from app.services.portfolio_upstream_payloads import build_safe_upstream_error_detail


def build_transaction_ledger_response(
    *,
    context: PortfolioTransactionsRequestContext,
    contract_version: str,
    result_payload: dict[str, Any],
) -> PortfolioTransactionLedgerResponse:
    transactions = parse_transaction_views(result_payload)
    return PortfolioTransactionLedgerResponse(
        correlation_id=context.correlation_id,
        contract_version=contract_version,
        portfolio_id=context.portfolio_id,
        as_of_date=(
            str(result_payload.get("as_of_date"))
            if result_payload.get("as_of_date")
            else context.as_of_date
        ),
        include_projected=context.include_projected,
        total=int(result_payload.get("total", len(transactions))),
        skip=int(result_payload.get("skip", context.skip)),
        limit=int(result_payload.get("limit", context.limit)),
        transactions=transactions,
    )


def parse_transaction_views(payload: dict[str, Any]) -> list[PortfolioTransactionView]:
    return [
        parse_transaction_view(item)
        for item in payload.get("transactions", [])
        if isinstance(item, dict)
    ]


def parse_transaction_view(item: dict[str, Any]) -> PortfolioTransactionView:
    return PortfolioTransactionView(
        transaction_id=str(item.get("transaction_id", "")),
        transaction_date=parse_transaction_timestamp(
            item.get("transaction_date"),
            field_name="transaction_date",
        ),
        settlement_date=parse_transaction_timestamp(
            item.get("settlement_date"),
            field_name="settlement_date",
            required=False,
        ),
        transaction_type=str(item.get("transaction_type", "")),
        component_type=optional_str(item.get("component_type")),
        security_id=str(item.get("security_id", "")),
        instrument_id=str(item.get("instrument_id", "")),
        quantity=float(quantize_quantity(item.get("quantity", 0))),
        price=float(quantize_price(item.get("price", 0)))
        if item.get("price") is not None
        else None,
        gross_amount=optional_money(item.get("gross_transaction_amount")),
        currency=optional_str(item.get("currency")),
        net_cost_base=optional_money(item.get("net_cost")),
        realized_gain_loss_base=optional_money(item.get("realized_gain_loss")),
        settlement_status=optional_str(item.get("settlement_status")),
        source_system=optional_str(item.get("source_system")),
        cash_entry_mode=optional_str(item.get("cash_entry_mode")),
        economic_event_id=optional_str(item.get("economic_event_id")),
        linked_transaction_group_id=optional_str(item.get("linked_transaction_group_id")),
        fx_contract_id=optional_str(item.get("fx_contract_id")),
        swap_event_id=optional_str(item.get("swap_event_id")),
        near_leg_group_id=optional_str(item.get("near_leg_group_id")),
        far_leg_group_id=optional_str(item.get("far_leg_group_id")),
    )


def optional_money(value: Any) -> float | None:
    if value is None:
        return None
    return float(quantize_money(value))


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def require_transaction_record_payload(
    *,
    status_code: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Map the source record read to distinct caller-visible failure states."""

    if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "portfolio_transaction_access_denied",
                "message": "lotus-core denied access to the requested portfolio transaction.",
            },
        )
    if status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "portfolio_transaction_not_found",
                "message": (
                    "No transaction with this identifier is visible within the requested portfolio."
                ),
            },
        )
    if status_code in (status.HTTP_400_BAD_REQUEST, 422):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "portfolio_transaction_request_invalid",
                "message": build_safe_upstream_error_detail(
                    "lotus-core rejected the transaction-record request",
                    payload,
                ),
            },
        )
    if status_code >= status.HTTP_400_BAD_REQUEST or not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "portfolio_transaction_source_unavailable",
                "message": "lotus-core could not return the requested transaction record.",
            },
        )
    return payload


def build_transaction_record_response(
    *,
    portfolio_id: str,
    transaction_id: str,
    correlation_id: str,
    contract_version: str,
    result_payload: dict[str, Any],
) -> PortfolioTransactionRecordResponse:
    record_payload = result_payload.get("transaction")
    if not isinstance(record_payload, dict):
        raise _transaction_record_identity_mismatch()
    transaction = parse_transaction_view(record_payload)
    if (
        optional_str(result_payload.get("portfolio_id")) != portfolio_id
        or transaction.transaction_id != transaction_id
    ):
        # A shape-valid record for another portfolio or transaction must never be
        # acknowledged as the caller's record; Workbench must not detect the mismatch.
        raise _transaction_record_identity_mismatch()
    return PortfolioTransactionRecordResponse(
        correlation_id=correlation_id,
        contract_version=contract_version,
        portfolio_id=portfolio_id,
        reporting_currency=optional_str(result_payload.get("reporting_currency")),
        transaction=transaction,
        reason_codes=[
            code for code in result_payload.get("reason_codes", []) if isinstance(code, str)
        ],
    )


def _transaction_record_identity_mismatch() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "code": "portfolio_transaction_record_identity_mismatch",
            "message": (
                "lotus-core returned a transaction record that does not match the requested "
                "portfolio and transaction identity."
            ),
        },
    )
