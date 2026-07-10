from __future__ import annotations

from typing import Any

from app.clients.advise_proposal_delivery_client import AdviseProposalDeliveryClientMixin


class AdviseProposalNarrativeClientMixin(AdviseProposalDeliveryClientMixin):
    async def regenerate_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative/regenerate",
            body=body,
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.narrative.regenerate",
        )

    async def get_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative",
            params={},
            headers=self._headers(correlation_id),
            operation="advise.advisory.proposals.narrative.get",
        )

    async def review_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        body: dict[str, Any],
        idempotency_key: str | None,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/advisory/proposals/{proposal_id}/versions/{version_no}/narrative/review",
            body=body,
            headers=self._optional_idempotency_headers(correlation_id, idempotency_key),
            operation="advise.advisory.proposals.narrative.review",
        )
