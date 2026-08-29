from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.contracts.proposal_memo_action_models import (
    ProposalMemoAiCommentaryResponse,
    ProposalMemoReportPackageEventResponse,
    ProposalMemoReportPackageResponse,
    ProposalMemoReviewResponse,
)
from app.contracts.proposal_memo_lineage_models import (
    ProposalMemoLineageResponse,
    ProposalMemoReplayEvidenceResponse,
)
from app.contracts.proposal_memo_models import ProposalMemoProjectionResponse, ProposalMemoResponse
from app.contracts.proposal_memos import ProposalMemoReportPackageEventEnvelopeResponse
from app.contracts.proposals import (
    ProposalMemoAiCommentaryEnvelopeResponse,
    ProposalMemoEnvelopeResponse,
    ProposalMemoLineageEnvelopeResponse,
    ProposalMemoProjectionEnvelopeResponse,
    ProposalMemoReplayEvidenceEnvelopeResponse,
    ProposalMemoReportPackageEnvelopeResponse,
    ProposalMemoReviewEnvelopeResponse,
)
from app.services.proposal_client_protocols import ProposalClient
from app.services.proposal_memo_errors import raise_proposal_memo_contract_invalid
from app.services.proposal_memo_source_contract import project_tolerant_memo_source_payload
from app.services.upstream_envelope import build_typed_gateway_envelope

EnvelopeT = TypeVar("EnvelopeT", bound=BaseModel)
PayloadT = TypeVar("PayloadT", bound=BaseModel)


def _build_typed_memo_envelope(
    response_model: type[EnvelopeT],
    payload_model: type[PayloadT],
    *,
    correlation_id: str,
    upstream_payload: dict[str, Any],
) -> EnvelopeT:
    try:
        published_payload = project_tolerant_memo_source_payload(payload_model, upstream_payload)
        return build_typed_gateway_envelope(
            response_model,
            payload_model,
            correlation_id=correlation_id,
            upstream_payload=published_payload.model_dump(mode="python"),
        )
    except ValidationError as exc:
        raise_proposal_memo_contract_invalid(exc)


def _validate_ai_commentary_request_identity(
    response: ProposalMemoAiCommentaryEnvelopeResponse,
    *,
    source_memo_hash: str,
    idempotency_key: str | None,
) -> ProposalMemoAiCommentaryEnvelopeResponse:
    posture = response.data.memo.ai_commentary_posture
    mismatched_fields: list[str] = []
    if response.data.memo.memo_hash != source_memo_hash:
        mismatched_fields.append("memo_hash")
    if posture.source_memo_hash != source_memo_hash:
        mismatched_fields.append("source_memo_hash")
    if idempotency_key is not None and posture.idempotency_key != idempotency_key:
        mismatched_fields.append("idempotency_key")
    if mismatched_fields:
        raise_proposal_memo_contract_invalid(
            ValueError(
                "AI commentary response did not match the submitted action identity: "
                + ", ".join(mismatched_fields)
            )
        )
    return response


class ProposalMemoServiceMixin:
    _advise_client: ProposalClient

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
        return _build_typed_memo_envelope(
            ProposalMemoEnvelopeResponse,
            ProposalMemoResponse,
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
        return _build_typed_memo_envelope(
            ProposalMemoEnvelopeResponse,
            ProposalMemoResponse,
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
        return _build_typed_memo_envelope(
            ProposalMemoProjectionEnvelopeResponse,
            ProposalMemoProjectionResponse,
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
        return _build_typed_memo_envelope(
            ProposalMemoReviewEnvelopeResponse,
            ProposalMemoReviewResponse,
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
    ) -> ProposalMemoReportPackageEventEnvelopeResponse:
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
        return _build_typed_memo_envelope(
            ProposalMemoReportPackageEventEnvelopeResponse,
            ProposalMemoReportPackageEventResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

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
        return _build_typed_memo_envelope(
            ProposalMemoReportPackageEnvelopeResponse,
            ProposalMemoReportPackageResponse,
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
        response = _build_typed_memo_envelope(
            ProposalMemoAiCommentaryEnvelopeResponse,
            ProposalMemoAiCommentaryResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )
        return _validate_ai_commentary_request_identity(
            response,
            source_memo_hash=body["source_memo_hash"],
            idempotency_key=idempotency_key,
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
        return _build_typed_memo_envelope(
            ProposalMemoLineageEnvelopeResponse,
            ProposalMemoLineageResponse,
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
        return _build_typed_memo_envelope(
            ProposalMemoReplayEvidenceEnvelopeResponse,
            ProposalMemoReplayEvidenceResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )
