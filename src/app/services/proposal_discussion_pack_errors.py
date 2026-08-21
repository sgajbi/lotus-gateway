from typing import NoReturn

from fastapi import HTTPException, status


def raise_proposal_discussion_pack_contract_invalid(
    exc: Exception | None = None,
) -> NoReturn:
    error = HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "source_service": "lotus-advise",
            "upstream_status": status.HTTP_502_BAD_GATEWAY,
            "error_code": "ADVISE_PROPOSAL_DISCUSSION_PACK_CONTRACT_INVALID",
            "detail": "lotus-advise discussion-pack evidence did not match the governed contract.",
        },
    )
    if exc is None:
        raise error
    raise error from exc


__all__ = ["raise_proposal_discussion_pack_contract_invalid"]
