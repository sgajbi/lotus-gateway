from typing import NoReturn

from fastapi import HTTPException, status


def raise_advisor_cockpit_action_contract_invalid(
    exc: Exception | None = None,
) -> NoReturn:
    """Fail closed when a successful Advise action payload is not safely consumable."""

    error = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": "lotus-advise",
            "upstream_status": status.HTTP_200_OK,
            "error_code": "ADVISE_COCKPIT_ACTION_CONTRACT_INVALID",
            "detail": (
                "lotus-advise advisor cockpit action data did not match the governed contract."
            ),
        },
    )
    if exc is None:
        raise error
    raise error from exc


__all__ = ["raise_advisor_cockpit_action_contract_invalid"]
