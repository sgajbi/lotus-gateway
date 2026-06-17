from fastapi.testclient import TestClient

from app.main import app


def test_advisory_copilot_routes_forward_to_advise_without_rewriting(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_supportability(self, correlation_id):  # noqa: ANN001
        _ = self
        captured["supportability"] = {"correlation_id": correlation_id}
        return 200, {
            "support_status": "ADVISE_COPILOT_GATEWAY_WORKBENCH_CANONICAL_PROOF_SUPPORTED",
            "client_ready_publication": "BLOCKED",
            "supported_action_families": ["PROPOSAL_EXPLANATION"],
            "unsupported_capability_boundaries": ["CLIENT_READY_PUBLICATION"],
        }

    async def _fake_create_packet(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["create_packet"] = {"body": body, "correlation_id": correlation_id}
        return 201, {"evidence_packet": {"evidence_packet_id": "packet-direct"}}

    async def _fake_create_packet_from_version(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["create_packet_from_version"] = {"body": body, "correlation_id": correlation_id}
        return 201, {
            "evidence_packet": {
                "evidence_packet_id": "packet-version",
                "evidence_packet_hash": "sha256:packet",
            }
        }

    async def _fake_get_packet(self, evidence_packet_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["get_packet"] = {
            "evidence_packet_id": evidence_packet_id,
            "correlation_id": correlation_id,
        }
        return 200, {"evidence_packet": {"evidence_packet_id": evidence_packet_id}}

    async def _fake_run_action(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["run_action"] = {
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {
            "run": {
                "run_id": "copilot-run-001",
                "review_posture": "REVIEW_REQUIRED",
                "client_ready_publication": "BLOCKED",
            }
        }

    async def _fake_get_run(self, run_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["get_run"] = {"run_id": run_id, "correlation_id": correlation_id}
        return 200, {"run": {"run_id": run_id}}

    async def _fake_review_run(self, run_id, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["review_run"] = {
            "run_id": run_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {
            "run": {"run_id": run_id, "review_posture": "APPROVED_FOR_INTERNAL_USE"},
            "review": {"review_id": "review-001"},
        }

    async def _fake_list_runs(  # noqa: ANN001
        self,
        proposal_id,
        version_id,
        params,
        correlation_id,
    ):
        _ = self
        captured["list_runs"] = {
            "proposal_id": proposal_id,
            "version_id": version_id,
            "params": params,
            "correlation_id": correlation_id,
        }
        return 200, {"items": [{"run_id": "copilot-run-001"}], "next_cursor": None}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_advisory_copilot_supportability",
        _fake_supportability,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_advisory_copilot_evidence_packet",
        _fake_create_packet,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient."
        "create_advisory_copilot_evidence_packet_from_proposal_version",
        _fake_create_packet_from_version,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_advisory_copilot_evidence_packet",
        _fake_get_packet,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.run_advisory_copilot_action",
        _fake_run_action,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_advisory_copilot_run",
        _fake_get_run,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.review_advisory_copilot_run",
        _fake_review_run,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.list_advisory_copilot_proposal_version_runs",
        _fake_list_runs,
    )

    client = TestClient(app)
    supportability_response = client.get(
        "/api/v1/advisory-copilot/supportability",
        headers={"X-Correlation-Id": "corr-copilot-support"},
    )
    create_packet_response = client.post(
        "/api/v1/advisory-copilot/evidence-packets",
        json={"body": {"action_family": "PROPOSAL_EXPLANATION"}},
        headers={"X-Correlation-Id": "corr-copilot-packet"},
    )
    version_packet_response = client.post(
        "/api/v1/advisory-copilot/evidence-packets/from-proposal-version",
        json={
            "body": {
                "proposal_id": "proposal-001",
                "proposal_version_no": 1,
                "action_family": "PROPOSAL_EXPLANATION",
            }
        },
        headers={"X-Correlation-Id": "corr-copilot-version-packet"},
    )
    get_packet_response = client.get(
        "/api/v1/advisory-copilot/evidence-packets/packet-version",
        headers={"X-Correlation-Id": "corr-copilot-get-packet"},
    )
    run_response = client.post(
        "/api/v1/advisory-copilot/actions",
        json={"body": {"evidence_packet_id": "packet-version"}},
        headers={
            "Idempotency-Key": "idem-copilot-action",
            "X-Correlation-Id": "corr-copilot-run",
        },
    )
    get_run_response = client.get(
        "/api/v1/advisory-copilot/actions/copilot-run-001",
        headers={"X-Correlation-Id": "corr-copilot-get-run"},
    )
    review_response = client.post(
        "/api/v1/advisory-copilot/actions/copilot-run-001/reviews",
        json={"body": {"action": "APPROVE_FOR_INTERNAL_USE"}},
        headers={
            "Idempotency-Key": "idem-copilot-review",
            "X-Correlation-Id": "corr-copilot-review",
        },
    )
    list_runs_response = client.get(
        "/api/v1/advisory-copilot/proposals/proposal-001/versions/version-001/runs",
        params={"limit": "10", "cursor": "cursor-1"},
        headers={"X-Correlation-Id": "corr-copilot-list-runs"},
    )

    assert supportability_response.status_code == 200
    assert create_packet_response.status_code == 201
    assert version_packet_response.status_code == 201
    assert get_packet_response.status_code == 200
    assert run_response.status_code == 200
    assert get_run_response.status_code == 200
    assert review_response.status_code == 200
    assert list_runs_response.status_code == 200
    assert supportability_response.json()["data"]["client_ready_publication"] == "BLOCKED"
    assert version_packet_response.json()["data"]["evidence_packet"]["evidence_packet_hash"] == (
        "sha256:packet"
    )
    assert run_response.json()["data"]["run"]["review_posture"] == "REVIEW_REQUIRED"
    assert review_response.json()["data"]["review"]["review_id"] == "review-001"
    assert list_runs_response.json()["data"]["items"][0]["run_id"] == "copilot-run-001"
    assert captured == {
        "supportability": {"correlation_id": "corr-copilot-support"},
        "create_packet": {
            "body": {"action_family": "PROPOSAL_EXPLANATION"},
            "correlation_id": "corr-copilot-packet",
        },
        "create_packet_from_version": {
            "body": {
                "proposal_id": "proposal-001",
                "proposal_version_no": 1,
                "action_family": "PROPOSAL_EXPLANATION",
            },
            "correlation_id": "corr-copilot-version-packet",
        },
        "get_packet": {
            "evidence_packet_id": "packet-version",
            "correlation_id": "corr-copilot-get-packet",
        },
        "run_action": {
            "body": {"evidence_packet_id": "packet-version"},
            "idempotency_key": "idem-copilot-action",
            "correlation_id": "corr-copilot-run",
        },
        "get_run": {"run_id": "copilot-run-001", "correlation_id": "corr-copilot-get-run"},
        "review_run": {
            "run_id": "copilot-run-001",
            "body": {"action": "APPROVE_FOR_INTERNAL_USE"},
            "idempotency_key": "idem-copilot-review",
            "correlation_id": "corr-copilot-review",
        },
        "list_runs": {
            "proposal_id": "proposal-001",
            "version_id": "version-001",
            "params": {"limit": 10, "cursor": "cursor-1"},
            "correlation_id": "corr-copilot-list-runs",
        },
    }


def test_advisory_copilot_supportability_openapi_documents_source_boundary() -> None:
    schema = app.openapi()
    supportability_operation = schema["paths"]["/api/v1/advisory-copilot/supportability"]["get"]
    action_operation = schema["paths"]["/api/v1/advisory-copilot/actions"]["post"]
    review_operation = schema["paths"]["/api/v1/advisory-copilot/actions/{run_id}/reviews"]["post"]
    runs_operation = schema["paths"][
        "/api/v1/advisory-copilot/proposals/{proposal_id}/versions/{version_id}/runs"
    ]["get"]

    assert "unsupported claim boundaries" in supportability_operation["description"]
    assert "does not execute AI workflow packs locally" in action_operation["description"]
    assert "internal-use posture only" in review_operation["description"]
    assert "does not rebuild copilot lineage" in runs_operation["description"]
