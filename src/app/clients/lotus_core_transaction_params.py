from typing import Any


def build_portfolio_transaction_query_params(
    *,
    limit: int,
    skip: int,
    sort_by: str,
    sort_order: str,
    include_projected: bool,
    as_of_date: str | None,
    transaction_type: str | None,
    security_id: str | None,
    instrument_id: str | None,
    component_type: str | None,
    linked_transaction_group_id: str | None,
    fx_contract_id: str | None,
    swap_event_id: str | None,
    near_leg_group_id: str | None,
    far_leg_group_id: str | None,
    start_date: str | None,
    end_date: str | None,
    reporting_currency: str | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "limit": limit,
        "skip": skip,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "include_projected": str(include_projected).lower(),
    }
    optional_params = {
        "as_of_date": as_of_date,
        "transaction_type": transaction_type,
        "security_id": security_id,
        "instrument_id": instrument_id,
        "component_type": component_type,
        "linked_transaction_group_id": linked_transaction_group_id,
        "fx_contract_id": fx_contract_id,
        "swap_event_id": swap_event_id,
        "near_leg_group_id": near_leg_group_id,
        "far_leg_group_id": far_leg_group_id,
        "start_date": start_date,
        "end_date": end_date,
        "reporting_currency": reporting_currency,
    }
    params.update({key: value for key, value in optional_params.items() if value is not None})
    return params
