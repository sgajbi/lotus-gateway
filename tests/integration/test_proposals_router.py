import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_proposal_simulate_success(monkeypatch):
    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 200, {"status": "READY", "proposal_run_id": "pr_1"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.simulate_proposal",
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


def test_proposal_simulate_forwards_upstream_error(monkeypatch):
    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 409, {"detail": "conflict"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.simulate_proposal",
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
        "app.clients.dpm_client.DpmClient.create_proposal",
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
        "app.clients.dpm_client.DpmClient.list_proposals",
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
        "app.clients.dpm_client.DpmClient.list_proposals",
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
        "app.clients.dpm_client.DpmClient.get_proposal",
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
        "app.clients.dpm_client.DpmClient.get_proposal",
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
        "app.clients.dpm_client.DpmClient.get_proposal_version",
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
        "app.clients.dpm_client.DpmClient.get_proposal_version",
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
        "app.clients.dpm_client.DpmClient.create_proposal_version",
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
        "app.clients.dpm_client.DpmClient.transition_proposal",
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
        "app.clients.dpm_client.DpmClient.transition_proposal",
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
        "app.clients.dpm_client.DpmClient.record_approval",
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
        "app.clients.dpm_client.DpmClient.record_approval",
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
        "app.clients.dpm_client.DpmClient.record_approval",
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
        "app.clients.dpm_client.DpmClient.get_workflow_events",
        _fake_get_workflow_events,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_approvals",
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
        "app.clients.dpm_client.DpmClient.get_proposal_lineage",
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
        "app.clients.dpm_client.DpmClient.get_proposal_lineage",
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
        "app.clients.dpm_client.DpmClient.get_workflow_events",
        _fake_get_workflow_events,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_approvals",
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
