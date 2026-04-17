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
        return 200, {"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}

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
            "items": [{"proposal_id": "pp_1", "current_state": "DRAFT"}],
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
        return 200, {"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_proposal",
        _fake_get_proposal,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals/pp_1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["current_state"] == "DRAFT"


def test_get_proposal_preserves_query_context(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_get_proposal(self, proposal_id, include_evidence, correlation_id):  # noqa: ANN001
        _ = self
        captured["proposal_id"] = proposal_id
        captured["include_evidence"] = include_evidence
        captured["correlation_id"] = correlation_id
        return 200, {"proposal": {"proposal_id": proposal_id, "current_state": "DRAFT"}}

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
        return 200, {"proposal_id": "pp_1", "version_no": 2, "status_at_creation": "DRAFT"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_proposal_version",
        _fake_get_proposal_version,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals/pp_1/versions/2?include_evidence=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["version_no"] == 2


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
        return 200, {"proposal_id": proposal_id, "version_no": version_no}

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
        return 200, {"proposal_id": "pp_1", "current_version_no": 2}

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
    assert payload["data"]["current_version_no"] == 2


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
        return 200, {"proposal_id": proposal_id, "current_state": "RISK_REVIEW"}

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
        return 200, {"proposal_id": proposal_id, "current_state": "AWAITING_CLIENT_CONSENT"}

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


def test_approve_compliance_success(monkeypatch):
    async def _fake_record_approval(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        assert body["approval_type"] == "COMPLIANCE"
        assert body["expected_state"] == "COMPLIANCE_REVIEW"
        assert idempotency_key == "idem-approve-compliance-1"
        return 200, {"proposal_id": proposal_id, "current_state": "AWAITING_CLIENT_CONSENT"}

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


def test_record_client_consent_success(monkeypatch):
    async def _fake_record_approval(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, proposal_id, correlation_id
        assert idempotency_key == "idem-consent-1"
        assert body["approval_type"] == "CLIENT_CONSENT"
        return 200, {"current_state": "EXECUTION_READY"}

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
        return 200, {"events": [{"event_type": "CREATED"}]}

    async def _fake_get_approvals(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        return 200, {"approvals": [{"approval_type": "RISK", "approved": True}]}

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
    assert events.json()["data"]["events"][0]["event_type"] == "CREATED"
    assert approvals.json()["data"]["approvals"][0]["approval_type"] == "RISK"


def test_workflow_events_and_approvals_preserve_query_context(monkeypatch):
    captured: dict[str, dict[str, str]] = {}

    async def _fake_get_workflow_events(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["events"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {"events": []}

    async def _fake_get_approvals(self, proposal_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["approvals"] = {
            "proposal_id": proposal_id,
            "correlation_id": correlation_id,
        }
        return 200, {"approvals": []}

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
