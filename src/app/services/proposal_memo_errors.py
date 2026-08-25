from typing import NoReturn

from fastapi import HTTPException, status


def raise_proposal_memo_contract_invalid(exc: Exception | None = None) -> NoReturn:
    """Map a successful but malformed Advise memo response to a product-safe 502."""

    error = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": "lotus-advise",
            "upstream_status": status.HTTP_200_OK,
            "error_code": "ADVISE_PROPOSAL_MEMO_CONTRACT_INVALID",
            "detail": "lotus-advise proposal memo evidence did not match the governed contract.",
        },
    )
    if exc is None:
        raise error
    raise error from exc


__all__ = ["raise_proposal_memo_contract_invalid"]
