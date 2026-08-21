import pytest
from fastapi import HTTPException

from app.services.proposal_service import ProposalService
from tests.shared.proposal_risk_impact_payload import build_proposal_risk_impact_source_payload


class _ProposalRiskImpactClient:
    def __init__(self, *, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls: list[dict[str, object]] = []

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "proposal_id": proposal_id,
                "include_evidence": include_evidence,
                "correlation_id": correlation_id,
            }
        )
        if self.status_code >= 400:
            return self.status_code, {"detail": "Proposal source is unavailable."}
        return self.status_code, build_proposal_risk_impact_source_payload(proposal_id=proposal_id)


@pytest.mark.asyncio
async def test_service_uses_one_bounded_detail_read_without_requesting_opaque_evidence() -> None:
    client = _ProposalRiskImpactClient()
    service = ProposalService(advise_client=client)  # type: ignore[arg-type]

    response = await service.get_proposal_risk_impact(
        proposal_id="pp_risk_001",
        correlation_id="corr-risk-impact-001",
    )

    assert response.contract_version == "proposal-risk-impact.v1"
    assert response.correlation_id == "corr-risk-impact-001"
    assert response.data.overall_state == "ready"
    assert client.calls == [
        {
            "proposal_id": "pp_risk_001",
            "include_evidence": False,
            "correlation_id": "corr-risk-impact-001",
        }
    ]


@pytest.mark.asyncio
async def test_service_preserves_product_safe_upstream_failure() -> None:
    client = _ProposalRiskImpactClient(status_code=503)
    service = ProposalService(advise_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_proposal_risk_impact(
            proposal_id="pp_risk_001",
            correlation_id="corr-risk-impact-002",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 503,
        "error_code": "ADVISE_PROPOSAL_UPSTREAM_ERROR",
        "detail": "lotus-advise proposal request failed.",
    }
