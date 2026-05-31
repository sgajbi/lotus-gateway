from typing import Any

from fastapi import status

from app.contracts.advisor_cockpit import AdvisorCockpitOwnerRole

ADVISOR_COCKPIT_READ_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Advisor cockpit action item was not found by lotus-advise."
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "lotus-advise rejected the cockpit request validation context."
    },
}
ADVISOR_COCKPIT_ACKNOWLEDGEMENT_RESPONSES: dict[int | str, dict[str, Any]] = {
    **ADVISOR_COCKPIT_READ_RESPONSES,
    status.HTTP_409_CONFLICT: {
        "description": "lotus-advise rejected a conflicting acknowledgement idempotency key."
    },
}


def cockpit_params(
    *,
    portfolio_id: str | None,
    advisor_id: str | None,
    role: AdvisorCockpitOwnerRole,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "portfolio_id": portfolio_id,
        "advisor_id": advisor_id,
        "role": role,
        "limit": limit,
        "cursor": cursor,
    }
    return {key: value for key, value in params.items() if value is not None}
