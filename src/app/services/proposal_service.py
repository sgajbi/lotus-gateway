from typing import Any

from app.contracts.proposals import (
    ProposalCreateData,
    ProposalCreateEnvelopeResponse,
    ProposalDetailData,
    ProposalDetailEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalListData,
    ProposalListEnvelopeResponse,
    ProposalSimulateResponse,
    ProposalSimulationData,
    ProposalVersionData,
    ProposalVersionEnvelopeResponse,
)
from app.services.proposal_client_protocols import ProposalClient
from app.services.proposal_delivery_service import ProposalDeliveryServiceMixin
from app.services.proposal_lifecycle_query_service import ProposalLifecycleQueryServiceMixin
from app.services.proposal_memo_service import ProposalMemoServiceMixin
from app.services.proposal_transition_service import ProposalTransitionServiceMixin
from app.services.upstream_envelope import (
    build_gateway_envelope,
    build_typed_gateway_envelope,
    raise_product_safe_service_error,
)


class ProposalService(
    ProposalTransitionServiceMixin,
    ProposalLifecycleQueryServiceMixin,
    ProposalMemoServiceMixin,
    ProposalDeliveryServiceMixin,
):
    def __init__(self, advise_client: ProposalClient):
        self._advise_client = advise_client

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalSimulateResponse:
        upstream_status, upstream_payload = await self._advise_client.simulate_proposal(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalSimulateResponse,
            ProposalSimulationData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def create_proposal_artifact(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_artifact(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalCreateEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalCreateEnvelopeResponse,
            ProposalCreateData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def list_proposals(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> ProposalListEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.list_proposals(
            params=filters,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalListEnvelopeResponse,
            ProposalListData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> ProposalDetailEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal(
            proposal_id=proposal_id,
            include_evidence=include_evidence,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalDetailEnvelopeResponse,
            ProposalDetailData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> ProposalVersionEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_version(
            proposal_id=proposal_id,
            version_no=version_no,
            include_evidence=include_evidence,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalVersionEnvelopeResponse,
            ProposalVersionData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalCreateEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_version(
            proposal_id=proposal_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_typed_gateway_envelope(
            ProposalCreateEnvelopeResponse,
            ProposalCreateData,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def create_proposal_async(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_async(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def create_proposal_version_async(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_proposal_version_async(
            proposal_id=proposal_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def get_proposal_operation(
        self,
        operation_id: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_proposal_operation(
            operation_id=operation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def get_proposal_operation_by_correlation(
        self,
        operation_correlation_id: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_proposal_operation_by_correlation(
            operation_correlation_id=operation_correlation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def get_proposal_operation_replay_evidence(
        self,
        operation_id: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_proposal_operation_replay_evidence(
            operation_id=operation_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def get_proposal_version_replay_evidence(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_proposal_version_replay_evidence(
            proposal_id=proposal_id,
            version_no=version_no,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def get_proposal_idempotency_record(
        self,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._advise_client.get_proposal_idempotency_record(
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    def _opaque_envelope(
        self,
        correlation_id: str,
        upstream_payload: dict[str, Any],
    ) -> ProposalEnvelopeResponse:
        return build_gateway_envelope(
            ProposalEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    def _raise_for_upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> None:
        raise_product_safe_service_error(
            upstream_status,
            upstream_payload,
            source_service="lotus-advise",
            error_code="ADVISE_PROPOSAL_UPSTREAM_ERROR",
            default_detail="lotus-advise proposal request failed.",
        )
