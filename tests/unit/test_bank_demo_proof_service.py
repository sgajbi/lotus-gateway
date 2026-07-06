import pytest
from fastapi import HTTPException

from app.services.bank_demo_proof_service import BankDemoProofService


class _FakeAdviseClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.status = 200
        self.payload: dict[str, object] = {
            "scenario_id": "RFC28_BANK_DEMO_CLIENT_READY_PROOF_CANONICAL",
            "primary_portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "proof_marker": "BANK_DEMO_PROOF_PACK_CREATED",
        }

    async def get_bank_demo_proof_scenario_contract(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(("scenario", {"correlation_id": correlation_id}))
        return self.status, self.payload

    async def get_bank_demo_supported_claim_register(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(("claims", {"correlation_id": correlation_id}))
        return self.status, self.payload

    async def build_bank_demo_proof_pack(
        self,
        *,
        body: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(("proof_pack", {"body": body, "correlation_id": correlation_id}))
        return self.status, self.payload


@pytest.mark.asyncio
async def test_bank_demo_proof_service_preserves_advise_owned_claim_posture() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.payload = {
        "claims": [
            {
                "claim_id": "advisor_journey_backend_evidence_available",
                "classification": "BACKEND_BACKED_UI_PENDING",
            },
            {
                "claim_id": "client_ready_publication_blocked",
                "classification": "UNSUPPORTED",
            },
        ]
    }
    service = BankDemoProofService(advise_client=advise_client)

    response = await service.get_supported_claim_register(correlation_id="corr-rfc0028-claims")

    assert response.correlation_id == "corr-rfc0028-claims"
    assert response.data == advise_client.payload
    assert response.data["claims"][0]["classification"] == "BACKEND_BACKED_UI_PENDING"
    assert response.data["claims"][1]["classification"] == "UNSUPPORTED"
    assert advise_client.calls == [("claims", {"correlation_id": "corr-rfc0028-claims"})]


@pytest.mark.asyncio
async def test_bank_demo_proof_service_forwards_sanitized_capture_request() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.payload = {
        "proof_pack": {
            "proof_marker": "BANK_DEMO_PROOF_PACK_CREATED",
            "client_ready_posture": "CLIENT_READY_PUBLICATION_BLOCKED",
        },
        "sanitized_runtime_summary": {"primary_portfolio_id": "PB_SG_GLOBAL_BAL_001"},
    }
    service = BankDemoProofService(advise_client=advise_client)

    response = await service.build_proof_pack(
        body={"live_runtime_payload": {"parity": {}}, "runtime_posture": {"endpoints": []}},
        correlation_id="corr-rfc0028-proof",
    )

    assert response.data == advise_client.payload
    assert response.data["proof_pack"]["client_ready_posture"] == (
        "CLIENT_READY_PUBLICATION_BLOCKED"
    )
    assert advise_client.calls == [
        (
            "proof_pack",
            {
                "body": {
                    "live_runtime_payload": {"parity": {}},
                    "runtime_posture": {"endpoints": []},
                },
                "correlation_id": "corr-rfc0028-proof",
            },
        )
    ]


@pytest.mark.asyncio
async def test_bank_demo_proof_service_maps_advise_material_drift_conflict() -> None:
    advise_client = _FakeAdviseClient()
    advise_client.status = 409
    advise_client.payload = {
        "detail": "RFC0028_BACKEND_PROOF_MATERIAL_REVIEW_BLOCKED: policy_evaluation='APPROVED'",
        "primary_portfolio_id": "PB_SENSITIVE",
        "runtime_payload": {"client_name": "Sensitive Client"},
    }
    service = BankDemoProofService(advise_client=advise_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.build_proof_pack(body={}, correlation_id="corr-rfc0028-proof")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "source_service": "lotus-advise",
        "upstream_status": 409,
        "error_code": "ADVISE_BANK_DEMO_PROOF_UPSTREAM_ERROR",
        "detail": "lotus-advise bank-demo proof request failed.",
    }
