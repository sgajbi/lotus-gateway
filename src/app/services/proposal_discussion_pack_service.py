import asyncio
from typing import Any

from app.contracts.proposal_discussion_pack import (
    ProposalDiscussionPackEnvelopeResponse,
)
from app.services.proposal_client_protocols import ProposalClient
from app.services.proposal_discussion_pack_projection import (
    ProposalDiscussionSourceResponse,
    project_proposal_discussion_pack,
)


class ProposalDiscussionPackServiceMixin:
    _advise_client: ProposalClient

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    async def get_proposal_discussion_pack(
        self,
        *,
        proposal_id: str,
        portfolio_id: str,
        version_no: int,
        correlation_id: str,
    ) -> ProposalDiscussionPackEnvelopeResponse:
        results = await self._read_discussion_pack_sources(
            proposal_id=proposal_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )
        detail_status, detail_payload = results[0]
        self._raise_for_upstream_error(detail_status, detail_payload)
        return _discussion_pack_envelope(
            results=results,
            proposal_id=proposal_id,
            portfolio_id=portfolio_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )

    async def _read_discussion_pack_sources(
        self,
        *,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[tuple[int, dict[str, Any]], ...]:
        return await asyncio.gather(
            self._advise_client.get_proposal(
                proposal_id=proposal_id,
                include_evidence=False,
                correlation_id=correlation_id,
            ),
            self._advise_client.get_proposal_narrative(
                proposal_id=proposal_id,
                version_no=version_no,
                correlation_id=correlation_id,
            ),
            self._advise_client.get_proposal_memo(
                proposal_id=proposal_id,
                version_no=version_no,
                correlation_id=correlation_id,
            ),
            self._advise_client.get_approvals(
                proposal_id=proposal_id,
                correlation_id=correlation_id,
            ),
            self._advise_client.get_delivery_summary(
                proposal_id=proposal_id,
                correlation_id=correlation_id,
            ),
        )


def _discussion_pack_envelope(
    *,
    results: tuple[tuple[int, dict[str, Any]], ...],
    proposal_id: str,
    portfolio_id: str,
    version_no: int,
    correlation_id: str,
) -> ProposalDiscussionPackEnvelopeResponse:
    detail, narrative, memo, approvals, delivery = results
    return ProposalDiscussionPackEnvelopeResponse(
        correlation_id=correlation_id,
        data=project_proposal_discussion_pack(
            detail_payload=detail[1],
            narrative_response=_source_response(narrative),
            memo_response=_source_response(memo),
            approvals_response=_source_response(approvals),
            delivery_response=_source_response(delivery),
            expected_proposal_id=proposal_id,
            expected_portfolio_id=portfolio_id,
            expected_version_no=version_no,
            correlation_id=correlation_id,
        ),
    )


def _source_response(
    result: tuple[int, dict[str, Any]],
) -> ProposalDiscussionSourceResponse:
    status_code, payload = result
    return ProposalDiscussionSourceResponse(status_code=status_code, payload=payload)


__all__ = ["ProposalDiscussionPackServiceMixin"]
