from fastapi.testclient import TestClient

from app.main import app


def test_policy_pack_routes_forward_to_advise_with_idempotency(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_list(self, correlation_id):  # noqa: ANN001
        _ = self
        captured["list"] = {"correlation_id": correlation_id}
        return 200, {"items": [{"policy_pack_id": "policy_pack_sg_private_banking"}]}

    async def _fake_get(self, policy_pack_id, policy_version, correlation_id):  # noqa: ANN001
        _ = self
        captured["get"] = {
            "policy_pack_id": policy_pack_id,
            "policy_version": policy_version,
            "correlation_id": correlation_id,
        }
        return 200, {"policy_pack_id": policy_pack_id, "policy_version": policy_version}

    async def _fake_validate(
        self,
        policy_pack_id,
        policy_version,
        body,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["validate"] = {
            "policy_pack_id": policy_pack_id,
            "policy_version": policy_version,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"validation_status": "PASSED", "policy_pack_id": policy_pack_id}

    async def _fake_activate(
        self,
        policy_pack_id,
        policy_version,
        body,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["activate"] = {
            "policy_pack_id": policy_pack_id,
            "policy_version": policy_version,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"activation_status": "ACTIVE", "policy_version": policy_version}

    monkeypatch.setattr("app.clients.advise_client.AdviseClient.list_policy_packs", _fake_list)
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_policy_pack_version",
        _fake_get,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.validate_policy_pack_version",
        _fake_validate,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.activate_policy_pack_version",
        _fake_activate,
    )

    client = TestClient(app)
    list_response = client.get(
        "/api/v1/advisory-policy-packs",
        headers={"X-Correlation-Id": "corr-policy-list"},
    )
    get_response = client.get(
        "/api/v1/advisory-policy-packs/policy_pack_sg_private_banking/versions/2026.05",
        headers={"X-Correlation-Id": "corr-policy-get"},
    )
    validate_response = client.post(
        "/api/v1/advisory-policy-packs/policy_pack_sg_private_banking/versions/2026.05/validate",
        json={"body": {"validated_by": "policy_admin_1", "scope": "pre-activation"}},
        headers={
            "Idempotency-Key": "idem-policy-validate",
            "X-Correlation-Id": "corr-policy-validate",
        },
    )
    activate_response = client.post(
        "/api/v1/advisory-policy-packs/policy_pack_sg_private_banking/versions/2026.05/activate",
        json={"body": {"activated_by": "policy_admin_1", "reason": "monthly release"}},
        headers={
            "Idempotency-Key": "idem-policy-activate",
            "X-Correlation-Id": "corr-policy-activate",
        },
    )

    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert validate_response.status_code == 200
    assert activate_response.status_code == 200
    assert captured == {
        "list": {"correlation_id": "corr-policy-list"},
        "get": {
            "policy_pack_id": "policy_pack_sg_private_banking",
            "policy_version": "2026.05",
            "correlation_id": "corr-policy-get",
        },
        "validate": {
            "policy_pack_id": "policy_pack_sg_private_banking",
            "policy_version": "2026.05",
            "body": {"validated_by": "policy_admin_1", "scope": "pre-activation"},
            "idempotency_key": "idem-policy-validate",
            "correlation_id": "corr-policy-validate",
        },
        "activate": {
            "policy_pack_id": "policy_pack_sg_private_banking",
            "policy_version": "2026.05",
            "body": {"activated_by": "policy_admin_1", "reason": "monthly release"},
            "idempotency_key": "idem-policy-activate",
            "correlation_id": "corr-policy-activate",
        },
    }
    assert validate_response.json()["data"]["validation_status"] == "PASSED"


def test_policy_evaluation_routes_preserve_advise_boundary_and_blockers(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_create(
        self,
        proposal_id,
        proposal_version_id,
        body,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["create"] = {
            "proposal_id": proposal_id,
            "proposal_version_id": proposal_version_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 201, {
            "evaluation_id": "pev_001",
            "evaluation_status": "PENDING_REVIEW",
            "client_ready": {
                "status": "BLOCKED",
                "blockers": ["requires_compliance_signoff"],
            },
        }

    async def _fake_queue(self, evaluation_status, portfolio_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["queue"] = {
            "evaluation_status": evaluation_status,
            "portfolio_id": portfolio_id,
            "correlation_id": correlation_id,
        }
        return 200, {"items": [{"evaluation_id": "pev_001", "queue": "Compliance"}]}

    async def _fake_workflow(self, evaluation_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["workflow"] = {"evaluation_id": evaluation_id, "correlation_id": correlation_id}
        return 200, {"evaluation_id": evaluation_id, "required_roles": ["COMPLIANCE"]}

    async def _fake_sign_off_package(self, evaluation_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["sign_off_package"] = {
            "evaluation_id": evaluation_id,
            "correlation_id": correlation_id,
        }
        return 200, {"evaluation_id": evaluation_id, "client_ready": {"status": "BLOCKED"}}

    async def _fake_ai_evidence(
        self,
        evaluation_id,
        body,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["ai_evidence"] = {
            "evaluation_id": evaluation_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {
            "evaluation_id": evaluation_id,
            "ai_evidence": {
                "status": "UNAVAILABLE",
                "non_authoritative": True,
            },
            "client_ready": {
                "status": "BLOCKED",
                "blockers": ["ai_evidence_unavailable"],
            },
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_policy_evaluation",
        _fake_create,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_policy_review_queue",
        _fake_queue,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_policy_evaluation_workflow",
        _fake_workflow,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_policy_sign_off_package",
        _fake_sign_off_package,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.request_policy_ai_evidence",
        _fake_ai_evidence,
    )

    client = TestClient(app)
    create_response = client.post(
        "/api/v1/proposals/pp_001/versions/ppv_001/policy-evaluations",
        json={"body": {"requested_by": "advisor_1", "policy_pack_id": "policy_pack_sg"}},
        headers={
            "Idempotency-Key": "idem-policy-create",
            "X-Correlation-Id": "corr-policy-create",
        },
    )
    queue_response = client.get(
        "/api/v1/advisory-policy-evaluations/review-queue"
        "?evaluation_status=PENDING_REVIEW&portfolio_id=PB_SG_GLOBAL_BAL_001",
        headers={"X-Correlation-Id": "corr-policy-queue"},
    )
    workflow_response = client.get(
        "/api/v1/advisory-policy-evaluations/pev_001/workflow",
        headers={"X-Correlation-Id": "corr-policy-workflow"},
    )
    sign_off_response = client.get(
        "/api/v1/advisory-policy-evaluations/pev_001/sign-off-package",
        headers={"X-Correlation-Id": "corr-policy-signoff-package"},
    )
    ai_response = client.post(
        "/api/v1/advisory-policy-evaluations/pev_001/ai-evidence",
        json={"body": {"requested_by": "advisor_1", "purpose": "draft review"}},
        headers={
            "Idempotency-Key": "idem-policy-ai",
            "X-Correlation-Id": "corr-policy-ai",
        },
    )

    assert create_response.status_code == 200
    assert queue_response.status_code == 200
    assert workflow_response.status_code == 200
    assert sign_off_response.status_code == 200
    assert ai_response.status_code == 200
    assert create_response.json()["data"]["client_ready"] == {
        "status": "BLOCKED",
        "blockers": ["requires_compliance_signoff"],
    }
    assert ai_response.json()["data"]["ai_evidence"]["non_authoritative"] is True
    assert ai_response.json()["data"]["client_ready"]["status"] == "BLOCKED"
    assert captured == {
        "create": {
            "proposal_id": "pp_001",
            "proposal_version_id": "ppv_001",
            "body": {"requested_by": "advisor_1", "policy_pack_id": "policy_pack_sg"},
            "idempotency_key": "idem-policy-create",
            "correlation_id": "corr-policy-create",
        },
        "queue": {
            "evaluation_status": "PENDING_REVIEW",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "correlation_id": "corr-policy-queue",
        },
        "workflow": {"evaluation_id": "pev_001", "correlation_id": "corr-policy-workflow"},
        "sign_off_package": {
            "evaluation_id": "pev_001",
            "correlation_id": "corr-policy-signoff-package",
        },
        "ai_evidence": {
            "evaluation_id": "pev_001",
            "body": {"requested_by": "advisor_1", "purpose": "draft review"},
            "idempotency_key": "idem-policy-ai",
            "correlation_id": "corr-policy-ai",
        },
    }


def test_policy_decision_report_event_lineage_and_replay_routes_forward_unchanged(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_get_evaluation(self, evaluation_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["get"] = {"evaluation_id": evaluation_id, "correlation_id": correlation_id}
        return 200, {"evaluation_id": evaluation_id, "evaluation_status": "BLOCKED"}

    async def _fake_replay(self, evaluation_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["replay"] = {
            "evaluation_id": evaluation_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {"evaluation_id": evaluation_id, "replay_status": "MATCHED"}

    async def _fake_event(self, evaluation_id, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["event"] = {
            "evaluation_id": evaluation_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"evaluation_id": evaluation_id, "event_recorded": True}

    async def _fake_lineage(self, evaluation_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["lineage"] = {"evaluation_id": evaluation_id, "correlation_id": correlation_id}
        return 200, {"evaluation_id": evaluation_id, "source_hashes": ["sha256:abc"]}

    async def _fake_decision(self, evaluation_id, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["decision"] = {
            "evaluation_id": evaluation_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"evaluation_id": evaluation_id, "decision_status": "RECORDED"}

    async def _fake_report(self, evaluation_id, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["report"] = {
            "evaluation_id": evaluation_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {"evaluation_id": evaluation_id, "report_package_status": "DRAFT"}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_policy_evaluation",
        _fake_get_evaluation,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.replay_policy_evaluation",
        _fake_replay,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.record_policy_evaluation_event",
        _fake_event,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_policy_evaluation_lineage",
        _fake_lineage,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.record_policy_sign_off_decision",
        _fake_decision,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.request_policy_report_package",
        _fake_report,
    )

    client = TestClient(app)
    get_response = client.get(
        "/api/v1/advisory-policy-evaluations/pev_001",
        headers={"X-Correlation-Id": "corr-policy-get-evaluation"},
    )
    replay_response = client.post(
        "/api/v1/advisory-policy-evaluations/pev_001/replay",
        json={"body": {"requested_by": "support_1"}},
        headers={"X-Correlation-Id": "corr-policy-replay"},
    )
    event_response = client.post(
        "/api/v1/advisory-policy-evaluations/pev_001/events",
        json={"body": {"event_type": "SUPERVISORY_NOTE", "actor_id": "supervisor_1"}},
        headers={
            "Idempotency-Key": "idem-policy-event",
            "X-Correlation-Id": "corr-policy-event",
        },
    )
    lineage_response = client.get(
        "/api/v1/advisory-policy-evaluations/pev_001/lineage",
        headers={"X-Correlation-Id": "corr-policy-lineage"},
    )
    decision_response = client.post(
        "/api/v1/advisory-policy-evaluations/pev_001/sign-off-decisions",
        json={"body": {"decision": "APPROVE", "decided_by": "compliance_1"}},
        headers={
            "Idempotency-Key": "idem-policy-decision",
            "X-Correlation-Id": "corr-policy-decision",
        },
    )
    report_response = client.post(
        "/api/v1/advisory-policy-evaluations/pev_001/report-packages",
        json={"body": {"audience": "CLIENT_DRAFT", "requested_by": "advisor_1"}},
        headers={
            "Idempotency-Key": "idem-policy-report",
            "X-Correlation-Id": "corr-policy-report",
        },
    )

    assert get_response.status_code == 200
    assert replay_response.status_code == 200
    assert event_response.status_code == 200
    assert lineage_response.status_code == 200
    assert decision_response.status_code == 200
    assert report_response.status_code == 200
    assert captured == {
        "get": {"evaluation_id": "pev_001", "correlation_id": "corr-policy-get-evaluation"},
        "replay": {
            "evaluation_id": "pev_001",
            "body": {"requested_by": "support_1"},
            "correlation_id": "corr-policy-replay",
        },
        "event": {
            "evaluation_id": "pev_001",
            "body": {"event_type": "SUPERVISORY_NOTE", "actor_id": "supervisor_1"},
            "idempotency_key": "idem-policy-event",
            "correlation_id": "corr-policy-event",
        },
        "lineage": {"evaluation_id": "pev_001", "correlation_id": "corr-policy-lineage"},
        "decision": {
            "evaluation_id": "pev_001",
            "body": {"decision": "APPROVE", "decided_by": "compliance_1"},
            "idempotency_key": "idem-policy-decision",
            "correlation_id": "corr-policy-decision",
        },
        "report": {
            "evaluation_id": "pev_001",
            "body": {"audience": "CLIENT_DRAFT", "requested_by": "advisor_1"},
            "idempotency_key": "idem-policy-report",
            "correlation_id": "corr-policy-report",
        },
    }
    assert lineage_response.json()["data"]["source_hashes"] == ["sha256:abc"]
