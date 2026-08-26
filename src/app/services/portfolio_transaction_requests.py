"""Request-shape mapping for Lotus Core portfolio transaction reads."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PortfolioTransactionsRequestContext:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    include_projected: bool
    skip: int
    limit: int
    transaction_type: str | None
    security_id: str | None
    instrument_id: str | None
    component_type: str | None
    linked_transaction_group_id: str | None
    fx_contract_id: str | None
    swap_event_id: str | None
    near_leg_group_id: str | None
    far_leg_group_id: str | None
    sort_by: str
    sort_order: str
    start_date: str | None
    end_date: str | None
    reporting_currency: str | None


@dataclass(frozen=True)
class PortfolioTransactionLedgerRequest:
    portfolio_id: str
    correlation_id: str
    as_of_date: str | None
    include_projected: bool
    skip: int
    limit: int
    transaction_type: str | None = None
    security_id: str | None = None
    instrument_id: str | None = None
    component_type: str | None = None
    linked_transaction_group_id: str | None = None
    fx_contract_id: str | None = None
    swap_event_id: str | None = None
    near_leg_group_id: str | None = None
    far_leg_group_id: str | None = None
    sort_by: str = "transaction_date"
    sort_order: str = "desc"
    start_date: str | None = None
    end_date: str | None = None
    reporting_currency: str | None = None


def build_portfolio_transactions_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str | None,
    include_projected: bool,
    skip: int,
    limit: int,
    transaction_type: str | None,
    security_id: str | None,
    instrument_id: str | None,
    component_type: str | None,
    linked_transaction_group_id: str | None,
    fx_contract_id: str | None,
    swap_event_id: str | None,
    near_leg_group_id: str | None,
    far_leg_group_id: str | None,
    sort_by: str,
    sort_order: str,
    start_date: str | None,
    end_date: str | None,
    reporting_currency: str | None,
) -> PortfolioTransactionsRequestContext:
    return PortfolioTransactionsRequestContext(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        as_of_date=as_of_date,
        include_projected=include_projected,
        skip=skip,
        limit=limit,
        transaction_type=transaction_type,
        security_id=security_id,
        instrument_id=instrument_id,
        component_type=component_type,
        linked_transaction_group_id=linked_transaction_group_id,
        fx_contract_id=fx_contract_id,
        swap_event_id=swap_event_id,
        near_leg_group_id=near_leg_group_id,
        far_leg_group_id=far_leg_group_id,
        sort_by=sort_by,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )


def build_transaction_ledger_request_context(
    request: PortfolioTransactionLedgerRequest,
) -> PortfolioTransactionsRequestContext:
    return build_portfolio_transactions_request_context(
        portfolio_id=request.portfolio_id,
        correlation_id=request.correlation_id,
        as_of_date=request.as_of_date,
        include_projected=request.include_projected,
        skip=request.skip,
        limit=request.limit,
        transaction_type=request.transaction_type,
        security_id=request.security_id,
        instrument_id=request.instrument_id,
        component_type=request.component_type,
        linked_transaction_group_id=request.linked_transaction_group_id,
        fx_contract_id=request.fx_contract_id,
        swap_event_id=request.swap_event_id,
        near_leg_group_id=request.near_leg_group_id,
        far_leg_group_id=request.far_leg_group_id,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        start_date=request.start_date,
        end_date=request.end_date,
        reporting_currency=request.reporting_currency,
    )


def build_transaction_rows_page_request_context(
    *,
    portfolio_id: str,
    correlation_id: str,
    as_of_date: str | None,
    skip: int,
    limit: int,
    start_date: str,
    end_date: str,
    reporting_currency: str | None,
) -> PortfolioTransactionsRequestContext:
    return build_portfolio_transactions_request_context(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        as_of_date=as_of_date,
        include_projected=False,
        skip=skip,
        limit=limit,
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
        sort_order="asc",
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )


def portfolio_transactions_cache_key(
    context: PortfolioTransactionsRequestContext,
) -> tuple[object, ...]:
    return (
        "transactions",
        context.portfolio_id,
        context.as_of_date,
        context.include_projected,
        context.skip,
        context.limit,
        context.transaction_type,
        context.security_id,
        context.instrument_id,
        context.component_type,
        context.linked_transaction_group_id,
        context.fx_contract_id,
        context.swap_event_id,
        context.near_leg_group_id,
        context.far_leg_group_id,
        context.sort_by,
        context.sort_order,
        context.start_date,
        context.end_date,
        context.reporting_currency,
    )


def portfolio_transactions_client_kwargs(
    context: PortfolioTransactionsRequestContext,
) -> dict[str, Any]:
    return {
        "portfolio_id": context.portfolio_id,
        "correlation_id": context.correlation_id,
        "as_of_date": context.as_of_date,
        "include_projected": context.include_projected,
        "skip": context.skip,
        "limit": context.limit,
        "sort_by": context.sort_by,
        "sort_order": context.sort_order,
        "transaction_type": context.transaction_type,
        "security_id": context.security_id,
        "instrument_id": context.instrument_id,
        "component_type": context.component_type,
        "linked_transaction_group_id": context.linked_transaction_group_id,
        "fx_contract_id": context.fx_contract_id,
        "swap_event_id": context.swap_event_id,
        "near_leg_group_id": context.near_leg_group_id,
        "far_leg_group_id": context.far_leg_group_id,
        "start_date": context.start_date,
        "end_date": context.end_date,
        "reporting_currency": context.reporting_currency,
    }
