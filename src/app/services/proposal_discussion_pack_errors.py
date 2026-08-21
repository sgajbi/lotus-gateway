from typing import NoReturn

from fastapi import HTTPException, status


class ProposalDiscussionPackSnapshotConflict(RuntimeError):
    """Signals a retryable disagreement between concurrently read source facts."""


def raise_proposal_discussion_pack_snapshot_conflict() -> NoReturn:
    raise ProposalDiscussionPackSnapshotConflict


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


__all__ = [
    "ProposalDiscussionPackSnapshotConflict",
    "raise_proposal_discussion_pack_contract_invalid",
    "raise_proposal_discussion_pack_snapshot_conflict",
]
