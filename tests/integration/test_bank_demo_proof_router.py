from fastapi.testclient import TestClient

from app.main import app


def test_bank_demo_proof_routes_forward_to_advise_without_rewriting(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_scenario(self, correlation_id):  # noqa: ANN001
        _ = self
        captured["scenario"] = {"correlation_id": correlation_id}
        return 200, {
            "scenario_id": "RFC28_BANK_DEMO_CLIENT_READY_PROOF_CANONICAL",
            "primary_portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "proof_marker": "BANK_DEMO_PROOF_PACK_CREATED",
        }

    async def _fake_claims(self, correlation_id):  # noqa: ANN001
        _ = self
        captured["claims"] = {"correlation_id": correlation_id}
        return 200, {
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

    async def _fake_proof_pack(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["proof_pack"] = {"body": body, "correlation_id": correlation_id}
        return 200, {
            "proof_pack": {
                "proof_marker": "BANK_DEMO_PROOF_PACK_CREATED",
                "client_ready_posture": "CLIENT_READY_PUBLICATION_BLOCKED",
            },
            "sanitized_runtime_summary": {
                "primary_portfolio_id": "PB_SG_GLOBAL_BAL_001",
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_bank_demo_proof_scenario_contract",
        _fake_scenario,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_bank_demo_supported_claim_register",
        _fake_claims,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.build_bank_demo_proof_pack",
        _fake_proof_pack,
    )

    client = TestClient(app)
    scenario_response = client.get(
        "/api/v1/advisory/bank-demo-proof/scenario-contract",
        headers={"X-Correlation-Id": "corr-rfc0028-scenario"},
    )
    claims_response = client.get(
        "/api/v1/advisory/bank-demo-proof/supported-claim-register",
        headers={"X-Correlation-Id": "corr-rfc0028-claims"},
    )
    proof_response = client.post(
        "/api/v1/advisory/bank-demo-proof/proof-packs",
        json={
            "live_runtime_payload": {
                "parity": {"complete_issuer_portfolio": "PB_SG_GLOBAL_BAL_001"}
            },
            "runtime_posture": {"endpoints": []},
        },
        headers={"X-Correlation-Id": "corr-rfc0028-proof"},
    )

    assert scenario_response.status_code == 200
    assert claims_response.status_code == 200
    assert proof_response.status_code == 200
    assert scenario_response.json()["data"]["scenario_id"] == (
        "RFC28_BANK_DEMO_CLIENT_READY_PROOF_CANONICAL"
    )
    assert claims_response.json()["data"]["claims"][0]["classification"] == (
        "BACKEND_BACKED_UI_PENDING"
    )
    assert proof_response.json()["data"]["proof_pack"]["client_ready_posture"] == (
        "CLIENT_READY_PUBLICATION_BLOCKED"
    )
    assert captured == {
        "scenario": {"correlation_id": "corr-rfc0028-scenario"},
        "claims": {"correlation_id": "corr-rfc0028-claims"},
        "proof_pack": {
            "body": {
                "live_runtime_payload": {
                    "parity": {"complete_issuer_portfolio": "PB_SG_GLOBAL_BAL_001"}
                },
                "runtime_posture": {"endpoints": []},
            },
            "correlation_id": "corr-rfc0028-proof",
        },
    }


def test_bank_demo_proof_router_preserves_advise_material_drift_error(monkeypatch):
    async def _fake_proof_pack(self, body, correlation_id):  # noqa: ANN001
        _ = self, body, correlation_id
        return 409, {
            "detail": (
                "RFC0028_BACKEND_PROOF_MATERIAL_REVIEW_BLOCKED: policy_evaluation='APPROVED'"
            )
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.build_bank_demo_proof_pack",
        _fake_proof_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/advisory/bank-demo-proof/proof-packs",
        json={"live_runtime_payload": {}, "runtime_posture": {"endpoints": []}},
        headers={"X-Correlation-Id": "corr-rfc0028-proof"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["detail"] == "lotus-advise bank-demo proof request failed."
