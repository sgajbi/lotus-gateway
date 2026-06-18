from typing import Any

from app.contracts.proposals import (
    ProposalEnvelopeResponse,
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoEnvelopeResponse,
    ProposalMemoLineageEnvelopeResponse,
    ProposalMemoProjectionEnvelopeResponse,
    ProposalMemoReplayEvidenceEnvelopeResponse,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReviewEnvelopeResponse,
)
from app.services.advisory_client_protocols import ProposalClient
from app.services.upstream_envelope import build_gateway_envelope


class ProposalMemoServiceMixin:
    _advise_client: ProposalClient

    def _opaque_envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> ProposalEnvelopeResponse:
        raise NotImplementedError

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    async def create_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalMemoEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_memo(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> ProposalMemoEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_memo(
            proposal_id=proposal_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_proposal_memo_projection(
        self,
        proposal_id: str,
        version_no: int,
        audience: str | None,
        correlation_id: str,
    ) -> ProposalMemoProjectionEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_memo_projection(
            proposal_id=proposal_id,
            version_no=version_no,
            audience=audience,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoProjectionEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def review_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalMemoReviewEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.review_proposal_memo(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoReviewEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def record_proposal_memo_report_package_event(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.record_proposal_memo_report_package_event(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def request_proposal_memo_report_package(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalMemoReportPackageEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.request_proposal_memo_report_package(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoReportPackageEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def request_proposal_memo_ai_commentary(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalMemoAiCommentaryEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.request_proposal_memo_ai_commentary(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoAiCommentaryEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_proposal_memo_lineage(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalMemoLineageEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_memo_lineage(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoLineageEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_proposal_memo_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> ProposalMemoReplayEvidenceEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_proposal_memo_replay_evidence(
            proposal_id=proposal_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalMemoReplayEvidenceEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )
