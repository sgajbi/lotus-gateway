from fastapi.testclient import TestClient

from app.main import app


def test_dpm_proof_pack_generate_preserves_manage_truth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_generate_proof_pack(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["idempotency_key"] = idempotency_key
        captured["correlation_id"] = correlation_id
        return 200, _proof_pack_payload()

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.generate_proof_pack",
        _fake_generate_proof_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/proof-packs",
        json={
            "idempotency_key": "idem-proof-pack-router-1",
            "body": {"source_type": "REBALANCE_RUN", "rebalance_run_id": "rr_001"},
        },
        headers={"X-Correlation-Id": "corr-proof-pack-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured == {
        "body": {"source_type": "REBALANCE_RUN", "rebalance_run_id": "rr_001"},
        "idempotency_key": "idem-proof-pack-router-1",
        "correlation_id": "corr-proof-pack-router-1",
    }
    assert payload["correlation_id"] == "corr-proof-pack-router-1"
    assert payload["source_service"] == "lotus-manage"
    assert payload["supportability"]["authority"] == "lotus-manage:RFC-0040"
    assert payload["supportability"]["proof_pack_id"] == "dpp_rr_001"
    assert payload["data"] == _proof_pack_payload()


def test_dpm_proof_pack_get_uses_manage_identifier(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_proof_pack(self, proof_pack_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["proof_pack_id"] = proof_pack_id
        captured["correlation_id"] = correlation_id
        return 200, _proof_pack_payload()

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_proof_pack", _fake_get_proof_pack)

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/proof-packs/dpp_rr_001",
        headers={"X-Correlation-Id": "corr-proof-pack-get-router-1"},
    )

    assert response.status_code == 200
    assert captured == {
        "proof_pack_id": "dpp_rr_001",
        "correlation_id": "corr-proof-pack-get-router-1",
    }
    assert response.json()["data"]["proof_pack"]["content_hash"] == "sha256:proof-pack"


def test_dpm_proof_pack_markdown_is_returned_in_gateway_envelope(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_proof_pack_markdown(self, proof_pack_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["proof_pack_id"] = proof_pack_id
        captured["correlation_id"] = correlation_id
        return 200, "# DPM proof pack\n", {}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_proof_pack_markdown",
        _fake_get_proof_pack_markdown,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/proof-packs/dpp_rr_001/summary.md",
        headers={"X-Correlation-Id": "corr-proof-pack-md-router-1"},
    )

    assert response.status_code == 200
    assert captured == {
        "proof_pack_id": "dpp_rr_001",
        "correlation_id": "corr-proof-pack-md-router-1",
    }
    assert response.json()["markdown"] == "# DPM proof pack\n"


def test_dpm_proof_pack_handoff_routes_preserve_manage_payload(monkeypatch) -> None:
    captured: list[dict[str, object]] = []

    async def _fake_report_input(self, proof_pack_id, correlation_id):  # noqa: ANN001
        _ = self
        captured.append(
            {
                "method": "report_input",
                "proof_pack_id": proof_pack_id,
                "correlation_id": correlation_id,
            }
        )
        return 200, {"proof_pack_id": proof_pack_id, "report_input_ref": "report-input:dpp_rr_001"}

    async def _fake_ai_input(self, proof_pack_id, correlation_id):  # noqa: ANN001
        _ = self
        captured.append(
            {
                "method": "ai_input",
                "proof_pack_id": proof_pack_id,
                "correlation_id": correlation_id,
            }
        )
        return 200, {"proof_pack_id": proof_pack_id, "ai_evidence_input_ref": "ai:dpp_rr_001"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_proof_pack_report_input",
        _fake_report_input,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_proof_pack_ai_evidence_input",
        _fake_ai_input,
    )

    client = TestClient(app)
    report_response = client.get(
        "/api/v1/dpm/command-center/proof-packs/dpp_rr_001/report-input",
        headers={"X-Correlation-Id": "corr-proof-pack-report-router-1"},
    )
    ai_response = client.get(
        "/api/v1/dpm/command-center/proof-packs/dpp_rr_001/ai-evidence-input",
        headers={"X-Correlation-Id": "corr-proof-pack-ai-router-1"},
    )

    assert report_response.status_code == 200
    assert ai_response.status_code == 200
    assert report_response.json()["data"]["report_input_ref"] == "report-input:dpp_rr_001"
    assert ai_response.json()["data"]["ai_evidence_input_ref"] == "ai:dpp_rr_001"
    assert captured == [
        {
            "method": "report_input",
            "proof_pack_id": "dpp_rr_001",
            "correlation_id": "corr-proof-pack-report-router-1",
        },
        {
            "method": "ai_input",
            "proof_pack_id": "dpp_rr_001",
            "correlation_id": "corr-proof-pack-ai-router-1",
        },
    ]


def _proof_pack_payload() -> dict[str, object]:
    return {
        "proof_pack": {
            "proof_pack_id": "dpp_rr_001",
            "status": "READY",
            "content_hash": "sha256:proof-pack",
            "source_hashes": {"mandate": "sha256:mandate"},
            "sections": [{"section_id": "mandate", "state": "READY"}],
        },
        "markdown_url": "/api/v1/rebalance/proof-packs/dpp_rr_001/summary.md",
    }
