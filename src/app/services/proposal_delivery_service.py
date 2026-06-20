from typing import Any

from app.contracts.proposals import (
    ProposalDeliveryEventsEnvelopeResponse,
    ProposalDeliverySummaryEnvelopeResponse,
    ProposalEnvelopeResponse,
    ProposalNarrativeReviewEnvelopeResponse,
    ProposalReportRequestEnvelopeResponse,
)
from app.services.proposal_client_protocols import ProposalClient
from app.services.upstream_envelope import build_gateway_envelope


class ProposalDeliveryServiceMixin:
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

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalNarrativeReviewEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.review_proposal_narrative(
            proposal_id=proposal_id,
            version_no=version_no,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalNarrativeReviewEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def create_report_request(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> ProposalReportRequestEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_report_request(
            proposal_id=proposal_id,
            body=body,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalReportRequestEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def create_execution_handoff(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.create_execution_handoff(
            proposal_id=proposal_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def get_delivery_summary(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalDeliverySummaryEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_delivery_summary(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalDeliverySummaryEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_delivery_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalDeliveryEventsEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_delivery_events(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return build_gateway_envelope(
            ProposalDeliveryEventsEnvelopeResponse,
            correlation_id=correlation_id,
            upstream_payload=upstream_payload,
        )

    async def get_execution_status(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.get_execution_status(
            proposal_id=proposal_id,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)

    async def record_execution_update(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> ProposalEnvelopeResponse:
        upstream_status, upstream_payload = await self._advise_client.record_execution_update(
            proposal_id=proposal_id,
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        self._raise_for_upstream_error(upstream_status, upstream_payload)
        return self._opaque_envelope(correlation_id, upstream_payload)
