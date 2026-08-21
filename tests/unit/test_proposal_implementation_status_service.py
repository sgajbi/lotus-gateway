from typing import cast

import pytest
from fastapi import HTTPException

from app.services.proposal_client_protocols import ProposalClient
from app.services.proposal_service import ProposalService
from tests.shared.proposal_implementation_status_payload import (
    build_proposal_implementation_status_source_payload,
)


class _ProposalImplementationStatusClient:
    def __init__(
        self,
        *,
        status_code: int = 200,
        source_proposal_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.source_proposal_id = source_proposal_id
        self.calls: list[dict[str, object]] = []

    async def get_execution_status(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "proposal_id": proposal_id,
                "correlation_id": correlation_id,
            }
        )
        if self.status_code >= 400:
            return self.status_code, {"detail": "Proposal implementation source is unavailable."}
        return self.status_code, build_proposal_implementation_status_source_payload(
            proposal_id=self.source_proposal_id or proposal_id,
        )


@pytest.mark.asyncio
async def test_service_returns_typed_source_bound_implementation_status() -> None:
    client = _ProposalImplementationStatusClient()
    service = ProposalService(advise_client=cast(ProposalClient, client))

    response = await service.get_execution_status(
        proposal_id="pp_implementation_001",
        correlation_id="corr-implementation-service",
    )

    assert response.contract_version == "proposal-implementation-status.v1"
    assert response.correlation_id == "corr-implementation-service"
    assert response.data.handoff_status == "ACCEPTED"
    assert response.data.lineage.gateway_correlation_id == "corr-implementation-service"
    assert client.calls == [
        {
            "proposal_id": "pp_implementation_001",
            "correlation_id": "corr-implementation-service",
        }
    ]


@pytest.mark.parametrize("status_code", [403, 404, 503])
@pytest.mark.asyncio
async def test_service_preserves_product_safe_upstream_failure(status_code: int) -> None:
    client = _ProposalImplementationStatusClient(status_code=status_code)
    service = ProposalService(advise_client=cast(ProposalClient, client))

    with pytest.raises(HTTPException) as exc_info:
        await service.get_execution_status(
            proposal_id="pp_implementation_001",
            correlation_id="corr-implementation-failure",
        )

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": status_code,
        "error_code": "ADVISE_PROPOSAL_UPSTREAM_ERROR",
        "detail": "lotus-advise proposal request failed.",
    }


@pytest.mark.asyncio
async def test_service_rejects_source_payload_for_a_different_proposal() -> None:
    client = _ProposalImplementationStatusClient(source_proposal_id="pp_other")
    service = ProposalService(advise_client=cast(ProposalClient, client))

    with pytest.raises(HTTPException) as exc_info:
        await service.get_execution_status(
            proposal_id="pp_implementation_001",
            correlation_id="corr-implementation-identity",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["error_code"] == (
        "ADVISE_PROPOSAL_IMPLEMENTATION_STATUS_CONTRACT_INVALID"
    )
