from typing import NoReturn

from fastapi import HTTPException, status


def raise_proposal_implementation_status_contract_invalid(
    exc: Exception | None = None,
) -> NoReturn:
    error = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": "lotus-advise",
            "upstream_status": status.HTTP_200_OK,
            "error_code": "ADVISE_PROPOSAL_IMPLEMENTATION_STATUS_CONTRACT_INVALID",
            "detail": "Proposal implementation evidence could not be safely verified.",
        },
    )
    if exc is None:
        raise error
    raise error from exc


__all__ = ["raise_proposal_implementation_status_contract_invalid"]
