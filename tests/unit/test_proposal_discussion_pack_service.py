from typing import Any, cast

import pytest
from fastapi import HTTPException

from app.services.proposal_client_protocols import ProposalClient
from app.services.proposal_service import ProposalService
from tests.shared.proposal_discussion_pack_payload import (
    build_discussion_pack_source_payloads,
)


class _DiscussionPackClient:
    def __init__(self, *, detail_status: int = 200) -> None:
        self.payloads = build_discussion_pack_source_payloads()
        self.detail_status = detail_status
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            (
                "detail",
                {
                    "proposal_id": proposal_id,
                    "include_evidence": include_evidence,
                    "correlation_id": correlation_id,
                },
            )
        )
        if self.detail_status >= 400:
            return self.detail_status, {"detail": "Proposal source unavailable."}
        return self.detail_status, self.payloads["detail"]

    async def get_proposal_narrative(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(("narrative", {"proposal_id": proposal_id, "version_no": version_no}))
        return 200, self.payloads["narrative"]

    async def get_proposal_memo(
        self,
        proposal_id: str,
        version_no: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(("memo", {"proposal_id": proposal_id, "version_no": version_no}))
        return 200, self.payloads["memo"]

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(("approvals", {"proposal_id": proposal_id}))
        return 200, self.payloads["approvals"]

    async def get_delivery_summary(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(("delivery", {"proposal_id": proposal_id}))
        return 200, self.payloads["delivery"]


@pytest.mark.asyncio
async def test_service_reads_one_selected_proposal_without_worklist_fan_out() -> None:
    client = _DiscussionPackClient()
    service = ProposalService(cast(ProposalClient, client))

    result = await service.get_proposal_discussion_pack(
        proposal_id="pp_discussion_001",
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        version_no=2,
        correlation_id="corr-discussion-service",
    )

    assert result.contract_version == "proposal-discussion-pack-review.v1"
    assert result.data.proposal_id == "pp_discussion_001"
    assert result.data.version_no == 2
    assert [name for name, _ in client.calls] == [
        "detail",
        "narrative",
        "memo",
        "approvals",
        "delivery",
    ]
    assert client.calls[0][1]["include_evidence"] is False


@pytest.mark.parametrize("status_code", [403, 404, 503])
@pytest.mark.asyncio
async def test_service_preserves_mandatory_proposal_source_failure(status_code: int) -> None:
    service = ProposalService(
        cast(ProposalClient, _DiscussionPackClient(detail_status=status_code))
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_proposal_discussion_pack(
            proposal_id="pp_discussion_001",
            portfolio_id="PB_SG_GLOBAL_BAL_001",
            version_no=2,
            correlation_id="corr-discussion-failure",
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail["source_service"] == "lotus-advise"
    assert exc_info.value.detail["error_code"] == "ADVISE_PROPOSAL_UPSTREAM_ERROR"
