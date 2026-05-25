import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_proposal_simulate_success(monkeypatch):
    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 200, {
            "proposal_run_id": "pr_1",
            "correlation_id": "corr_engine_1",
            "status": "READY",
            "before": {"portfolio_value": {"amount": "100000.00", "currency": "USD"}},
            "intents": [
                {
                    "intent_type": "CASH_FLOW",
                    "intent_id": "oi_cf_1",
                    "currency": "USD",
                    "amount": "2000.00",
                }
            ],
            "after_simulated": {"portfolio_value": {"amount": "102000.00", "currency": "USD"}},
            "reconciliation": {"cash_balance_delta": {"amount": "2000.00", "currency": "USD"}},
            "rule_results": [{"rule_id": "CASH_BAND", "severity": "SOFT", "status": "PASS"}],
            "explanation": {"summary": "Within mandate concentration limits."},
            "diagnostics": {
                "warnings": [],
                "data_quality": {"price_missing": [], "fx_missing": []},
            },
            "drift_analysis": {"tracking_error_pct": 1.2},
            "suitability": {"status": "PASS", "issues": []},
            "gate_decision": {
                "gate": "CLIENT_CONSENT_REQUIRED",
                "recommended_next_step": "REQUEST_CLIENT_CONSENT",
            },
            "lineage": {"request_hash": "sha256:req-1", "idempotency_key": "idem-1"},
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.simulate_proposal",
        _fake_simulate_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/simulate",
        json={
            "body": {
                "portfolio_snapshot": {"portfolio_id": "pf_1", "base_currency": "USD"},
                "market_data_snapshot": {"prices": [], "fx_rates": []},
                "shelf_entries": [],
                "proposed_cash_flows": [],
                "proposed_trades": [],
                "options": {"enable_proposal_simulation": True},
            }
        },
        headers={"Idempotency-Key": "idem-1", "X-Correlation-Id": "corr-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["correlation_id"] == "corr-1"
    assert payload["data"]["status"] == "READY"
    assert payload["data"]["proposal_run_id"] == "pr_1"
    assert payload["data"]["correlation_id"] == "corr_engine_1"
    assert payload["data"]["intents"][0]["intent_type"] == "CASH_FLOW"
    assert payload["data"]["diagnostics"]["data_quality"]["price_missing"] == []
    assert payload["data"]["gate_decision"]["gate"] == "CLIENT_CONSENT_REQUIRED"
    assert payload["data"]["lineage"]["idempotency_key"] == "idem-1"


def test_proposal_simulate_forwards_upstream_error(monkeypatch):
    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 409, {"detail": "conflict"}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.simulate_proposal",
        _fake_simulate_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/simulate",
        json={"body": {"options": {"enable_proposal_simulation": True}}},
        headers={"Idempotency-Key": "idem-1"},
    )

    assert response.status_code == 409


def test_proposal_simulate_requires_idempotency_header():
    client = TestClient(app)
    response = client.post("/api/v1/proposals/simulate", json={"body": {}})
    assert response.status_code == 422


def test_proposal_create_success(monkeypatch):
    async def _fake_create_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 1,
            },
            "version": {
                "proposal_version_id": "ppv_1",
                "proposal_id": "pp_1",
                "version_no": 1,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_1", "status": "READY"},
                "artifact": {"artifact_id": "artifact_1"},
                "evidence_bundle": {},
            },
            "latest_workflow_event": {
                "event_id": "pwe_1",
                "proposal_id": "pp_1",
                "event_type": "CREATED",
                "from_state": None,
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:00:00+00:00",
                "reason": {},
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_proposal",
        _fake_create_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals",
        json={
            "body": {
                "created_by": "advisor_1",
                "simulate_request": {"options": {"enable_proposal_simulation": True}},
            }
        },
        headers={"Idempotency-Key": "idem-create-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["proposal_id"] == "pp_1"
    assert payload["data"]["version"]["version_no"] == 1
    assert payload["data"]["latest_workflow_event"]["event_type"] == "CREATED"


def test_proposal_create_requires_idempotency_header():
    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals",
        json={"body": {"created_by": "advisor_1", "simulate_request": {"options": {}}}},
    )
    assert response.status_code == 422


def test_proposal_artifact_async_and_support_routes_preserve_advise_contract(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_artifact(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["artifact"] = {
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"artifact_id": "artifact_001", "artifact_hash": "sha256:artifact"}

    async def _fake_async(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["async"] = {
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 202, {"operation_id": "apo_001", "status": "ACCEPTED"}

    async def _fake_operation(self, operation_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["operation"] = {
            "operation_id": operation_id,
            "correlation_id": correlation_id,
        }
        return 200, {"operation_id": operation_id, "status": "SUCCEEDED"}

    async def _fake_version_replay(self, proposal_id, version_no, correlation_id):  # noqa: ANN001
        _ = self
        captured["version_replay"] = {
            "proposal_id": proposal_id,
            "version_no": version_no,
            "correlation_id": correlation_id,
        }
        return 200, {"proposal_id": proposal_id, "version_no": version_no, "replayable": True}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_proposal_artifact",
        _fake_artifact,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_proposal_async",
        _fake_async,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_operation",
        _fake_operation,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_version_replay_evidence",
        _fake_version_replay,
    )

    client = TestClient(app)
    artifact = client.post(
        "/api/v1/proposals/artifact",
        json={"body": {"proposal_run_id": "pr_001"}},
        headers={"Idempotency-Key": "idem-artifact", "X-Correlation-Id": "corr-artifact"},
    )
    async_create = client.post(
        "/api/v1/proposals/async",
        json={"body": {"created_by": "advisor_1"}},
        headers={"Idempotency-Key": "idem-async", "X-Correlation-Id": "corr-async"},
    )
    operation = client.get(
        "/api/v1/proposals/operations/apo_001",
        headers={"X-Correlation-Id": "corr-operation"},
    )
    replay = client.get(
        "/api/v1/proposals/pp_001/versions/2/replay-evidence",
        headers={"X-Correlation-Id": "corr-replay"},
    )

    assert artifact.status_code == 200
    assert async_create.status_code == 200
    assert operation.status_code == 200
    assert replay.status_code == 200
    assert captured == {
        "artifact": {
            "body": {"proposal_run_id": "pr_001"},
            "idempotency_key": "idem-artifact",
            "correlation_id": "corr-artifact",
        },
        "async": {
            "body": {"created_by": "advisor_1"},
            "idempotency_key": "idem-async",
            "correlation_id": "corr-async",
        },
        "operation": {"operation_id": "apo_001", "correlation_id": "corr-operation"},
        "version_replay": {
            "proposal_id": "pp_001",
            "version_no": 2,
            "correlation_id": "corr-replay",
        },
    }
    assert artifact.json()["data"]["artifact_hash"] == "sha256:artifact"
    assert async_create.json()["data"]["operation_id"] == "apo_001"
    assert operation.json()["data"]["status"] == "SUCCEEDED"
    assert replay.json()["data"]["replayable"] is True


def test_proposal_narrative_execution_and_memo_support_routes_forward_to_advise(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_regenerate_narrative(
        self,
        proposal_id,
        version_no,
        body,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["regenerate_narrative"] = {
            "proposal_id": proposal_id,
            "version_no": version_no,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {"narrative_id": "pn_candidate", "status": "READY_FOR_ADVISOR_REVIEW"}

    async def _fake_get_narrative(self, proposal_id, version_no, correlation_id):  # noqa: ANN001
        _ = self
        captured["get_narrative"] = {
            "proposal_id": proposal_id,
            "version_no": version_no,
            "correlation_id": correlation_id,
        }
        return 200, {"narrative_id": "pn_persisted", "review_state": "DRAFT"}

    async def _fake_handoff(
        self,
        proposal_id,
        body,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["execution_handoff"] = {
            "proposal_id": proposal_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"execution_request_id": "pex_001", "handoff_status": "REQUESTED"}

    async def _fake_execution_status(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["execution_status"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {"proposal_id": proposal_id, "handoff_status": "REQUESTED"}

    async def _fake_memo_report_event(
        self,
        proposal_id,
        version_no,
        body,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["memo_report_event"] = {
            "proposal_id": proposal_id,
            "version_no": version_no,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"event_id": "memo_report_event_001", "event_type": "ARCHIVED"}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.regenerate_proposal_narrative",
        _fake_regenerate_narrative,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_narrative",
        _fake_get_narrative,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_execution_handoff",
        _fake_handoff,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_execution_status",
        _fake_execution_status,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.record_proposal_memo_report_package_event",
        _fake_memo_report_event,
    )

    client = TestClient(app)
    regenerated = client.post(
        "/api/v1/proposals/pp_001/versions/2/narrative/regenerate",
        json={"body": {"requested_by": "advisor_1"}},
        headers={"X-Correlation-Id": "corr-narrative-regenerate"},
    )
    narrative = client.get(
        "/api/v1/proposals/pp_001/versions/2/narrative",
        headers={"X-Correlation-Id": "corr-narrative-read"},
    )
    handoff = client.post(
        "/api/v1/proposals/pp_001/execution-handoffs",
        json={"body": {"requested_by": "advisor_1", "execution_provider": "lotus-manage"}},
        headers={
            "Idempotency-Key": "idem-exec-handoff",
            "X-Correlation-Id": "corr-exec-handoff",
        },
    )
    execution_status = client.get(
        "/api/v1/proposals/pp_001/execution-status",
        headers={"X-Correlation-Id": "corr-exec-status"},
    )
    memo_event = client.post(
        "/api/v1/proposals/pp_001/versions/2/memo/report-package-events",
        json={"body": {"event_type": "ARCHIVED", "archive_ref": "archive_001"}},
        headers={
            "Idempotency-Key": "idem-memo-report-event",
            "X-Correlation-Id": "corr-memo-report-event",
        },
    )

    assert regenerated.status_code == 200
    assert narrative.status_code == 200
    assert handoff.status_code == 200
    assert execution_status.status_code == 200
    assert memo_event.status_code == 200
    assert captured == {
        "regenerate_narrative": {
            "proposal_id": "pp_001",
            "version_no": 2,
            "body": {"requested_by": "advisor_1"},
            "correlation_id": "corr-narrative-regenerate",
        },
        "get_narrative": {
            "proposal_id": "pp_001",
            "version_no": 2,
            "correlation_id": "corr-narrative-read",
        },
        "execution_handoff": {
            "proposal_id": "pp_001",
            "body": {"requested_by": "advisor_1", "execution_provider": "lotus-manage"},
            "idempotency_key": "idem-exec-handoff",
            "correlation_id": "corr-exec-handoff",
        },
        "execution_status": {
            "proposal_id": "pp_001",
            "correlation_id": "corr-exec-status",
        },
        "memo_report_event": {
            "proposal_id": "pp_001",
            "version_no": 2,
            "body": {"event_type": "ARCHIVED", "archive_ref": "archive_001"},
            "idempotency_key": "idem-memo-report-event",
            "correlation_id": "corr-memo-report-event",
        },
    }
    assert regenerated.json()["data"]["status"] == "READY_FOR_ADVISOR_REVIEW"
    assert handoff.json()["data"]["execution_request_id"] == "pex_001"
    assert memo_event.json()["data"]["event_type"] == "ARCHIVED"


def test_proposal_list_success(monkeypatch):
    async def _fake_list_proposals(self, params, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        assert params["state"] == "DRAFT"
        return 200, {
            "items": [
                {
                    "proposal_id": "pp_1",
                    "portfolio_id": "PF_1001",
                    "current_state": "DRAFT",
                    "current_version_no": 1,
                    "created_by": "advisor_1",
                }
            ],
            "next_cursor": None,
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.list_proposals",
        _fake_list_proposals,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals?state=DRAFT&limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["items"][0]["proposal_id"] == "pp_1"
    assert payload["data"]["items"][0]["portfolio_id"] == "PF_1001"
    assert payload["data"]["items"][0]["current_version_no"] == 1


def test_proposal_list_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_list_proposals(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {"items": [], "next_cursor": "pp_00042"}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.list_proposals",
        _fake_list_proposals,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/proposals"
        "?portfolio_id=PF_1001&state=DRAFT&created_by=advisor_1"
        "&created_from=2026-01-01&created_to=2026-03-31&limit=15&cursor=pp_00041",
        headers={"X-Correlation-Id": "corr-proposal-list"},
    )

    assert response.status_code == 200
    assert captured == {
        "params": {
            "portfolio_id": "PF_1001",
            "state": "DRAFT",
            "created_by": "advisor_1",
            "created_from": "2026-01-01",
            "created_to": "2026-03-31",
            "limit": 15,
            "cursor": "pp_00041",
        },
        "correlation_id": "corr-proposal-list",
    }
    assert response.json()["data"]["next_cursor"] == "pp_00042"


def test_get_proposal_success(monkeypatch):
    async def _fake_get_proposal(self, proposal_id, include_evidence, correlation_id):  # noqa: ANN001
        _ = self, include_evidence, correlation_id
        assert proposal_id == "pp_1"
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 2,
                "created_by": "advisor_1",
            },
            "current_version": {
                "proposal_version_id": "ppv_2",
                "proposal_id": "pp_1",
                "version_no": 2,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
                "artifact": {"artifact_id": "artifact_2"},
                "evidence_bundle": {"hashes": {"request_hash": "sha256:req-2"}},
            },
            "last_gate_decision": {
                "gate": "CLIENT_CONSENT_REQUIRED",
                "recommended_next_step": "REQUEST_CLIENT_CONSENT",
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal",
        _fake_get_proposal,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals/pp_1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["current_state"] == "DRAFT"
    assert payload["data"]["current_version"]["version_no"] == 2
    assert payload["data"]["last_gate_decision"]["gate"] == "CLIENT_CONSENT_REQUIRED"


def test_get_proposal_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_get_proposal(self, proposal_id, include_evidence, correlation_id):  # noqa: ANN001
        _ = self
        captured["proposal_id"] = proposal_id
        captured["include_evidence"] = include_evidence
        captured["correlation_id"] = correlation_id
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 1,
            },
            "current_version": {
                "proposal_version_id": "ppv_1",
                "proposal_id": proposal_id,
                "version_no": 1,
                "status_at_creation": "READY",
                "proposal_result": {},
                "artifact": {},
                "evidence_bundle": {},
            },
            "last_gate_decision": None,
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal",
        _fake_get_proposal,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/proposals/pp_1?include_evidence=true",
        headers={"X-Correlation-Id": "corr-proposal-detail"},
    )

    assert response.status_code == 200
    assert captured == {
        "proposal_id": "pp_1",
        "include_evidence": True,
        "correlation_id": "corr-proposal-detail",
    }


def test_get_proposal_version_success(monkeypatch):
    async def _fake_get_proposal_version(  # noqa: ANN001
        self, proposal_id, version_no, include_evidence, correlation_id
    ):
        _ = self, include_evidence, correlation_id
        assert proposal_id == "pp_1"
        assert version_no == 2
        return 200, {
            "proposal_version_id": "ppv_2",
            "proposal_id": "pp_1",
            "version_no": 2,
            "created_at": "2026-02-19T12:06:00+00:00",
            "request_hash": "sha256:req-2",
            "artifact_hash": "sha256:artifact-2",
            "simulation_hash": "sha256:sim-2",
            "status_at_creation": "READY",
            "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
            "artifact": {"artifact_id": "artifact_2"},
            "evidence_bundle": {"hashes": {"request_hash": "sha256:req-2"}},
            "gate_decision": {"gate": "EXECUTION_READY", "recommended_next_step": "EXECUTE"},
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_version",
        _fake_get_proposal_version,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals/pp_1/versions/2?include_evidence=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["version_no"] == 2
    assert payload["data"]["gate_decision"]["gate"] == "EXECUTION_READY"


def test_get_proposal_version_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_get_proposal_version(  # noqa: ANN001
        self, proposal_id, version_no, include_evidence, correlation_id
    ):
        _ = self
        captured["proposal_id"] = proposal_id
        captured["version_no"] = version_no
        captured["include_evidence"] = include_evidence
        captured["correlation_id"] = correlation_id
        return 200, {
            "proposal_version_id": "ppv_2",
            "proposal_id": proposal_id,
            "version_no": version_no,
            "status_at_creation": "READY",
            "proposal_result": {},
            "artifact": {},
            "evidence_bundle": {},
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_version",
        _fake_get_proposal_version,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/proposals/pp_1/versions/2?include_evidence=true",
        headers={"X-Correlation-Id": "corr-proposal-version"},
    )

    assert response.status_code == 200
    assert captured == {
        "proposal_id": "pp_1",
        "version_no": 2,
        "include_evidence": True,
        "correlation_id": "corr-proposal-version",
    }


def test_create_proposal_version_success(monkeypatch):
    async def _fake_create_proposal_version(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, idempotency_key, correlation_id
        assert proposal_id == "pp_1"
        assert body["created_by"] == "advisor_1"
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 2,
            },
            "version": {
                "proposal_version_id": "ppv_2",
                "proposal_id": "pp_1",
                "version_no": 2,
                "status_at_creation": "READY",
                "proposal_result": {"proposal_run_id": "pr_2", "status": "READY"},
                "artifact": {"artifact_id": "artifact_2"},
                "evidence_bundle": {},
            },
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "proposal_id": "pp_1",
                "event_type": "NEW_VERSION_CREATED",
                "from_state": "DRAFT",
                "to_state": "DRAFT",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:06:00+00:00",
                "reason": {},
                "related_version_no": 2,
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_proposal_version",
        _fake_create_proposal_version,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/versions",
        json={"body": {"created_by": "advisor_1", "simulate_request": {"options": {}}}},
        headers={"Idempotency-Key": "idem-v2"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["current_version_no"] == 2
    assert payload["data"]["version"]["version_no"] == 2
    assert payload["data"]["latest_workflow_event"]["event_type"] == "NEW_VERSION_CREATED"


def test_create_proposal_version_requires_idempotency_header():
    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/versions",
        json={"body": {"created_by": "advisor_1", "simulate_request": {"options": {}}}},
    )
    assert response.status_code == 422


def test_submit_proposal_success(monkeypatch):
    seen = {}

    async def _fake_transition_proposal(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, correlation_id
        seen["proposal_id"] = proposal_id
        seen["body"] = body
        seen["idempotency_key"] = idempotency_key
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "RISK_REVIEW",
            "latest_workflow_event": {
                "event_id": "pwe_2",
                "proposal_id": proposal_id,
                "event_type": "SUBMITTED_FOR_RISK_REVIEW",
                "from_state": "DRAFT",
                "to_state": "RISK_REVIEW",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:07:00+00:00",
                "reason": {"comment": "submit"},
            },
            "approval": None,
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.transition_proposal",
        _fake_transition_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/submit",
        json={
            "actor_id": "advisor_1",
            "expected_state": "DRAFT",
            "review_type": "RISK",
            "reason": {"comment": "submit"},
        },
        headers={"Idempotency-Key": "idem-submit-1"},
    )

    assert response.status_code == 200
    assert seen["proposal_id"] == "pp_1"
    assert seen["body"]["event_type"] == "SUBMITTED_FOR_RISK_REVIEW"
    assert seen["idempotency_key"] == "idem-submit-1"
    assert (
        response.json()["data"]["latest_workflow_event"]["event_type"]
        == "SUBMITTED_FOR_RISK_REVIEW"
    )


def test_submit_proposal_forwards_upstream_error(monkeypatch):
    async def _fake_transition_proposal(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, proposal_id, body, idempotency_key, correlation_id
        return 409, {"detail": "STATE_CONFLICT"}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.transition_proposal",
        _fake_transition_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/submit",
        json={"actor_id": "advisor_1", "expected_state": "DRAFT"},
        headers={"Idempotency-Key": "idem-submit-2"},
    )

    assert response.status_code == 409


def test_approve_risk_success(monkeypatch):
    async def _fake_record_approval(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        assert body["approval_type"] == "RISK"
        assert body["expected_state"] == "RISK_REVIEW"
        assert idempotency_key == "idem-approve-risk-1"
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "latest_workflow_event": {
                "event_id": "pwe_3",
                "proposal_id": proposal_id,
                "event_type": "RISK_APPROVED",
                "from_state": "RISK_REVIEW",
                "to_state": "AWAITING_CLIENT_CONSENT",
                "actor_id": "risk_1",
                "occurred_at": "2026-02-19T12:08:00+00:00",
                "reason": {},
            },
            "approval": {
                "approval_id": "pap_1",
                "proposal_id": proposal_id,
                "approval_type": "RISK",
                "approved": True,
                "actor_id": "risk_1",
                "occurred_at": "2026-02-19T12:08:00+00:00",
                "details": {"comment": "ok"},
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.record_approval",
        _fake_record_approval,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/approve-risk",
        json={"actor_id": "risk_1", "expected_state": "RISK_REVIEW", "details": {"comment": "ok"}},
        headers={"Idempotency-Key": "idem-approve-risk-1"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["current_state"] == "AWAITING_CLIENT_CONSENT"
    assert response.json()["data"]["approval"]["approval_type"] == "RISK"


def test_approve_compliance_success(monkeypatch):
    async def _fake_record_approval(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        assert body["approval_type"] == "COMPLIANCE"
        assert body["expected_state"] == "COMPLIANCE_REVIEW"
        assert idempotency_key == "idem-approve-compliance-1"
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "latest_workflow_event": {
                "event_id": "pwe_4",
                "proposal_id": proposal_id,
                "event_type": "COMPLIANCE_APPROVED",
                "from_state": "COMPLIANCE_REVIEW",
                "to_state": "AWAITING_CLIENT_CONSENT",
                "actor_id": "compliance_1",
                "occurred_at": "2026-02-19T12:09:00+00:00",
                "reason": {},
            },
            "approval": {
                "approval_id": "pap_2",
                "proposal_id": proposal_id,
                "approval_type": "COMPLIANCE",
                "approved": True,
                "actor_id": "compliance_1",
                "occurred_at": "2026-02-19T12:09:00+00:00",
                "details": {},
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.record_approval",
        _fake_record_approval,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/approve-compliance",
        json={"actor_id": "compliance_1", "expected_state": "COMPLIANCE_REVIEW"},
        headers={"Idempotency-Key": "idem-approve-compliance-1"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["approval"]["approval_type"] == "COMPLIANCE"


def test_record_client_consent_success(monkeypatch):
    async def _fake_record_approval(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, proposal_id, correlation_id
        assert idempotency_key == "idem-consent-1"
        assert body["approval_type"] == "CLIENT_CONSENT"
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "EXECUTION_READY",
            "latest_workflow_event": {
                "event_id": "pwe_5",
                "proposal_id": proposal_id,
                "event_type": "CLIENT_CONSENT_RECORDED",
                "from_state": "AWAITING_CLIENT_CONSENT",
                "to_state": "EXECUTION_READY",
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:10:00+00:00",
                "reason": {},
            },
            "approval": {
                "approval_id": "pap_3",
                "proposal_id": proposal_id,
                "approval_type": "CLIENT_CONSENT",
                "approved": True,
                "actor_id": "advisor_1",
                "occurred_at": "2026-02-19T12:10:00+00:00",
                "details": {},
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.record_approval",
        _fake_record_approval,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/record-client-consent",
        json={"actor_id": "advisor_1", "expected_state": "AWAITING_CLIENT_CONSENT"},
        headers={"Idempotency-Key": "idem-consent-1"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["current_state"] == "EXECUTION_READY"
    assert response.json()["data"]["approval"]["approval_type"] == "CLIENT_CONSENT"


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/v1/proposals/pp_1/submit", {"actor_id": "advisor_1", "expected_state": "DRAFT"}),
        (
            "/api/v1/proposals/pp_1/approve-risk",
            {"actor_id": "risk_1", "expected_state": "RISK_REVIEW"},
        ),
        (
            "/api/v1/proposals/pp_1/approve-compliance",
            {"actor_id": "compliance_1", "expected_state": "COMPLIANCE_REVIEW"},
        ),
        (
            "/api/v1/proposals/pp_1/record-client-consent",
            {"actor_id": "advisor_1", "expected_state": "AWAITING_CLIENT_CONSENT"},
        ),
    ],
)
def test_proposal_write_actions_require_idempotency_header(path, payload):
    client = TestClient(app)
    response = client.post(path, json=payload)
    assert response.status_code == 422


def test_workflow_events_and_approvals_success(monkeypatch):
    async def _fake_get_workflow_events(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "DRAFT",
            "events": [
                {
                    "event_id": "pwe_1",
                    "proposal_id": proposal_id,
                    "event_type": "CREATED",
                    "from_state": None,
                    "to_state": "DRAFT",
                    "actor_id": "advisor_1",
                    "occurred_at": "2026-02-19T12:00:00+00:00",
                    "reason": {},
                }
            ],
        }

    async def _fake_get_approvals(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        return 200, {
            "proposal_id": proposal_id,
            "current_state": "AWAITING_CLIENT_CONSENT",
            "approvals": [
                {
                    "approval_id": "pap_1",
                    "proposal_id": proposal_id,
                    "approval_type": "RISK",
                    "approved": True,
                    "actor_id": "risk_1",
                    "occurred_at": "2026-02-19T12:07:00+00:00",
                    "details": {"comment": "Within mandate"},
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_workflow_events",
        _fake_get_workflow_events,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_approvals",
        _fake_get_approvals,
    )

    client = TestClient(app)
    events = client.get("/api/v1/proposals/pp_1/workflow-events")
    approvals = client.get("/api/v1/proposals/pp_1/approvals")

    assert events.status_code == 200
    assert approvals.status_code == 200
    assert events.json()["data"]["current_state"] == "DRAFT"
    assert events.json()["data"]["events"][0]["event_type"] == "CREATED"
    assert approvals.json()["data"]["current_state"] == "AWAITING_CLIENT_CONSENT"
    assert approvals.json()["data"]["approvals"][0]["approval_type"] == "RISK"


def test_proposal_lineage_success(monkeypatch):
    async def _fake_get_proposal_lineage(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        return 200, {
            "proposal": {
                "proposal_id": "pp_1",
                "portfolio_id": "PF_1001",
                "current_state": "AWAITING_CLIENT_CONSENT",
                "current_version_no": 2,
            },
            "proposal_id": "pp_1",
            "versions": [
                {
                    "proposal_version_id": "ppv_1",
                    "version_no": 1,
                    "request_hash": "rh_1",
                    "simulation_hash": "sh_1",
                    "artifact_hash": "ah_1",
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_lineage",
        _fake_get_proposal_lineage,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals/pp_1/lineage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["proposal_id"] == "pp_1"
    assert payload["data"]["proposal_id"] == "pp_1"
    assert payload["data"]["versions"][0]["version_no"] == 1


def test_proposal_lineage_preserves_query_context(monkeypatch):
    captured: dict[str, str] = {}

    async def _fake_get_proposal_lineage(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["proposal_id"] = proposal_id
        captured["correlation_id"] = correlation_id
        return 200, {
            "proposal": {
                "proposal_id": proposal_id,
                "portfolio_id": "PF_1001",
                "current_state": "DRAFT",
                "current_version_no": 1,
            },
            "proposal_id": proposal_id,
            "versions": [],
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_proposal_lineage",
        _fake_get_proposal_lineage,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/proposals/pp_1/lineage",
        headers={"X-Correlation-Id": "corr-proposal-lineage"},
    )

    assert response.status_code == 200
    assert captured == {
        "proposal_id": "pp_1",
        "correlation_id": "corr-proposal-lineage",
    }


def test_workflow_events_and_approvals_preserve_query_context(monkeypatch):
    captured: dict[str, dict[str, str]] = {}

    async def _fake_get_workflow_events(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["events"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {"proposal_id": proposal_id, "current_state": "DRAFT", "events": []}

    async def _fake_get_approvals(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["approvals"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {"proposal_id": proposal_id, "current_state": "DRAFT", "approvals": []}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_workflow_events",
        _fake_get_workflow_events,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_approvals",
        _fake_get_approvals,
    )

    client = TestClient(app)
    events = client.get(
        "/api/v1/proposals/pp_1/workflow-events",
        headers={"X-Correlation-Id": "corr-proposal-events"},
    )
    approvals = client.get(
        "/api/v1/proposals/pp_1/approvals",
        headers={"X-Correlation-Id": "corr-proposal-approvals"},
    )

    assert events.status_code == 200
    assert approvals.status_code == 200
    assert captured == {
        "events": {
            "proposal_id": "pp_1",
            "correlation_id": "corr-proposal-events",
        },
        "approvals": {
            "proposal_id": "pp_1",
            "correlation_id": "corr-proposal-approvals",
        },
    }


def test_reviewed_narrative_gateway_routes_preserve_source_posture(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_review_proposal_narrative(
        self,
        proposal_id,
        version_no,
        body,
        idempotency_key,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["review"] = {
            "proposal_id": proposal_id,
            "version_no": version_no,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {
            "narrative_review": {
                "review_state": "APPROVED_FOR_ADVISOR_USE",
                "source_narrative_hash": "sha256:narrative-001",
                "guardrail_policy_version": "rfc0023.narrative.v1",
            }
        }

    async def _fake_create_report_request(
        self,
        proposal_id,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["report_request"] = {
            "proposal_id": proposal_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {
            "report_request_id": "prr_001",
            "status": "READY",
            "explanation": {
                "include_reviewed_narrative": True,
                "proposal_narrative_package": {
                    "package_status": "INCLUDED_REVIEWED_NARRATIVE",
                    "source_narrative_hash": "sha256:narrative-001",
                },
            },
        }

    async def _fake_get_delivery_summary(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["delivery_summary"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {
            "proposal_id": proposal_id,
            "reporting_summary": {
                "include_reviewed_narrative": True,
                "source_narrative_hash": "sha256:narrative-001",
            },
        }

    async def _fake_get_delivery_events(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["delivery_events"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {
            "proposal_id": proposal_id,
            "event_count": 2,
            "events": [
                {"event_type": "NARRATIVE_APPROVED_FOR_ADVISOR_USE"},
                {"event_type": "REPORT_REQUESTED"},
            ],
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.review_proposal_narrative",
        _fake_review_proposal_narrative,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_report_request",
        _fake_create_report_request,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_delivery_summary",
        _fake_get_delivery_summary,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_delivery_events",
        _fake_get_delivery_events,
    )

    client = TestClient(app)
    review = client.post(
        "/api/v1/proposals/pp_1/versions/2/narrative/review",
        json={
            "action": "APPROVE",
            "reviewed_by": "compliance_reviewer_001",
            "reason": "Evidence-grounded and suitable for advisor use.",
        },
        headers={
            "Idempotency-Key": "idem-narrative-review-001",
            "X-Correlation-Id": "corr-narrative-review",
        },
    )
    report_request = client.post(
        "/api/v1/proposals/pp_1/report-requests",
        json={
            "report_type": "PORTFOLIO_REVIEW",
            "requested_by": "advisor_1",
            "related_version_no": 2,
            "include_reviewed_narrative": True,
        },
        headers={"X-Correlation-Id": "corr-report-request"},
    )
    delivery_summary = client.get(
        "/api/v1/proposals/pp_1/delivery-summary",
        headers={"X-Correlation-Id": "corr-delivery-summary"},
    )
    delivery_events = client.get(
        "/api/v1/proposals/pp_1/delivery-events",
        headers={"X-Correlation-Id": "corr-delivery-events"},
    )

    assert review.status_code == 200
    assert report_request.status_code == 200
    assert delivery_summary.status_code == 200
    assert delivery_events.status_code == 200

    review_payload = review.json()["data"]["narrative_review"]
    report_payload = report_request.json()["data"]["explanation"]
    summary_payload = delivery_summary.json()["data"]["reporting_summary"]
    events_payload = delivery_events.json()["data"]

    assert review_payload["review_state"] == "APPROVED_FOR_ADVISOR_USE"
    assert review_payload["source_narrative_hash"] == "sha256:narrative-001"
    assert (
        report_payload["proposal_narrative_package"]["package_status"]
        == "INCLUDED_REVIEWED_NARRATIVE"
    )
    assert report_payload["proposal_narrative_package"]["source_narrative_hash"] == (
        "sha256:narrative-001"
    )
    assert summary_payload["include_reviewed_narrative"] is True
    assert summary_payload["source_narrative_hash"] == "sha256:narrative-001"
    assert events_payload["event_count"] == 2
    assert events_payload["events"][0]["event_type"] == "NARRATIVE_APPROVED_FOR_ADVISOR_USE"

    assert captured == {
        "review": {
            "proposal_id": "pp_1",
            "version_no": 2,
            "body": {
                "action": "APPROVE",
                "reviewed_by": "compliance_reviewer_001",
                "reason": "Evidence-grounded and suitable for advisor use.",
                "client_ready_release_requested": False,
            },
            "idempotency_key": "idem-narrative-review-001",
            "correlation_id": "corr-narrative-review",
        },
        "report_request": {
            "proposal_id": "pp_1",
            "body": {
                "report_type": "PORTFOLIO_REVIEW",
                "requested_by": "advisor_1",
                "related_version_no": 2,
                "include_execution_summary": True,
                "include_reviewed_narrative": True,
            },
            "correlation_id": "corr-report-request",
        },
        "delivery_summary": {
            "proposal_id": "pp_1",
            "correlation_id": "corr-delivery-summary",
        },
        "delivery_events": {
            "proposal_id": "pp_1",
            "correlation_id": "corr-delivery-events",
        },
    }
