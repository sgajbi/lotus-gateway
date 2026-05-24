from fastapi.testclient import TestClient

from app.main import app


def test_create_advisory_workspace_preserves_stateful_contract(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_create_workspace(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 201, {
            "workspace": {
                "workspace_id": "aws_001",
                "workspace_name": body["workspace_name"],
                "input_mode": "stateful",
                "created_by": body["created_by"],
                "created_at": "2026-05-24T09:00:00+00:00",
                "lifecycle_state": "ACTIVE",
                "stateful_input": body["stateful_input"],
                "draft_state": {"trade_drafts": [], "cash_flow_drafts": []},
                "resolved_context": {
                    "portfolio_id": body["stateful_input"]["portfolio_id"],
                    "as_of": body["stateful_input"]["as_of"],
                    "portfolio_snapshot_id": "lotus-core:portfolio:PB_SG_GLOBAL_BAL_001:2026-05-24",
                },
            }
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.create_advisory_workspace",
        _fake_create_workspace,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/advisory-workspaces",
        json={
            "body": {
                "workspace_name": "Smith Family Trust tactical rebalance draft",
                "created_by": "advisor_1",
                "input_mode": "stateful",
                "stateful_input": {
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "as_of": "2026-05-24",
                    "mandate_id": "mandate_growth_01",
                },
            }
        },
        headers={"X-Correlation-Id": "corr-workspace-create"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["correlation_id"] == "corr-workspace-create"
    assert payload["data"]["workspace"]["workspace_id"] == "aws_001"
    assert captured["body"] == {
        "workspace_name": "Smith Family Trust tactical rebalance draft",
        "created_by": "advisor_1",
        "input_mode": "stateful",
        "stateful_input": {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "as_of": "2026-05-24",
            "mandate_id": "mandate_growth_01",
        },
    }


def test_advisory_workspace_draft_action_and_handoff_preserve_advise_boundary(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_apply_action(self, workspace_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["draft_action"] = {
            "workspace_id": workspace_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {
            "workspace": {
                "workspace_id": workspace_id,
                "evaluation_summary": {
                    "status": "PENDING_REVIEW",
                    "blocking_issue_count": 0,
                    "review_issue_count": 1,
                    "impact_summary": {
                        "portfolio_value_delta_base_ccy": "1250.00",
                        "trade_count": 1,
                        "cash_flow_count": 0,
                    },
                },
            }
        }

    async def _fake_handoff(self, workspace_id, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["handoff"] = {
            "workspace_id": workspace_id,
            "body": body,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {
            "handoff_action": "CREATED_PROPOSAL",
            "proposal": {"proposal": {"proposal_id": "pp_001", "current_state": "DRAFT"}},
            "workspace": {"workspace_id": workspace_id},
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.apply_advisory_workspace_draft_action",
        _fake_apply_action,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.handoff_advisory_workspace",
        _fake_handoff,
    )

    client = TestClient(app)
    action = client.post(
        "/api/v1/advisory-workspaces/aws_001/draft-actions",
        json={
            "body": {
                "actor_id": "advisor_1",
                "action_type": "ADD_TRADE",
                "trade": {
                    "intent_type": "SECURITY_TRADE",
                    "side": "BUY",
                    "instrument_id": "AAPL",
                    "quantity": "25.0000",
                },
            }
        },
        headers={"X-Correlation-Id": "corr-workspace-action"},
    )
    handoff = client.post(
        "/api/v1/advisory-workspaces/aws_001/handoff",
        json={
            "body": {
                "handoff_by": "advisor_1",
                "metadata": {"title": "Smith Family Trust tactical rebalance"},
            }
        },
        headers={
            "Idempotency-Key": "idem-workspace-handoff",
            "X-Correlation-Id": "corr-workspace-handoff",
        },
    )

    assert action.status_code == 200
    assert handoff.status_code == 200
    assert captured["draft_action"] == {
        "workspace_id": "aws_001",
        "body": {
            "actor_id": "advisor_1",
            "action_type": "ADD_TRADE",
            "trade": {
                "intent_type": "SECURITY_TRADE",
                "side": "BUY",
                "instrument_id": "AAPL",
                "quantity": "25.0000",
            },
        },
        "correlation_id": "corr-workspace-action",
    }
    assert captured["handoff"] == {
        "workspace_id": "aws_001",
        "body": {
            "handoff_by": "advisor_1",
            "metadata": {"title": "Smith Family Trust tactical rebalance"},
        },
        "idempotency_key": "idem-workspace-handoff",
        "correlation_id": "corr-workspace-handoff",
    }
    assert handoff.json()["data"]["handoff_action"] == "CREATED_PROPOSAL"


def test_advisory_workspace_saved_version_compare_and_ai_routes_preserve_advise_boundary(
    monkeypatch,
):
    captured: dict[str, object] = {}

    async def _fake_list_saved_versions(self, workspace_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["saved_versions"] = {
            "workspace_id": workspace_id,
            "correlation_id": correlation_id,
        }
        return 200, {"items": [{"workspace_version_id": "awv_001", "version_label": "baseline"}]}

    async def _fake_replay(
        self,
        workspace_id,
        workspace_version_id,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["replay"] = {
            "workspace_id": workspace_id,
            "workspace_version_id": workspace_version_id,
            "correlation_id": correlation_id,
        }
        return 200, {"workspace_version_id": workspace_version_id, "replayable": True}

    async def _fake_resume(self, workspace_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["resume"] = {
            "workspace_id": workspace_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {
            "workspace_id": workspace_id,
            "resumed_version_id": body["workspace_version_id"],
        }

    async def _fake_compare(self, workspace_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["compare"] = {
            "workspace_id": workspace_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {"workspace_id": workspace_id, "comparison": {"trade_delta_count": 2}}

    async def _fake_rationale(self, workspace_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["rationale"] = {
            "workspace_id": workspace_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {"run_id": "packrun_workspace_001", "status": "REVIEW_REQUIRED"}

    async def _fake_review_rationale(self, workspace_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["review_rationale"] = {
            "workspace_id": workspace_id,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {"run_id": body["run_id"], "review_action": {"action_type": "APPROVE"}}

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.list_advisory_workspace_saved_versions",
        _fake_list_saved_versions,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient."
        "get_advisory_workspace_saved_version_replay_evidence",
        _fake_replay,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.resume_advisory_workspace",
        _fake_resume,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.compare_advisory_workspace",
        _fake_compare,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.request_advisory_workspace_rationale",
        _fake_rationale,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.review_advisory_workspace_rationale",
        _fake_review_rationale,
    )

    client = TestClient(app)
    saved_versions = client.get(
        "/api/v1/advisory-workspaces/aws_001/saved-versions",
        headers={"X-Correlation-Id": "corr-saved"},
    )
    replay = client.get(
        "/api/v1/advisory-workspaces/aws_001/saved-versions/awv_001/replay-evidence",
        headers={"X-Correlation-Id": "corr-replay"},
    )
    resume = client.post(
        "/api/v1/advisory-workspaces/aws_001/resume",
        json={"body": {"workspace_version_id": "awv_001", "actor_id": "advisor_1"}},
        headers={"X-Correlation-Id": "corr-resume"},
    )
    compare = client.post(
        "/api/v1/advisory-workspaces/aws_001/compare",
        json={"body": {"workspace_version_id": "awv_001"}},
        headers={"X-Correlation-Id": "corr-compare"},
    )
    rationale = client.post(
        "/api/v1/advisory-workspaces/aws_001/assistant/rationale",
        json={"body": {"requested_by": "advisor_1", "instruction": "Summarize impact."}},
        headers={"X-Correlation-Id": "corr-rationale"},
    )
    review_rationale = client.post(
        "/api/v1/advisory-workspaces/aws_001/assistant/rationale/review-actions",
        json={
            "body": {
                "run_id": "packrun_workspace_001",
                "action_type": "APPROVE",
                "reviewed_by": "advisor_1",
            }
        },
        headers={"X-Correlation-Id": "corr-review-rationale"},
    )

    assert saved_versions.status_code == 200
    assert replay.status_code == 200
    assert resume.status_code == 200
    assert compare.status_code == 200
    assert rationale.status_code == 200
    assert review_rationale.status_code == 200
    assert captured == {
        "saved_versions": {
            "workspace_id": "aws_001",
            "correlation_id": "corr-saved",
        },
        "replay": {
            "workspace_id": "aws_001",
            "workspace_version_id": "awv_001",
            "correlation_id": "corr-replay",
        },
        "resume": {
            "workspace_id": "aws_001",
            "body": {"workspace_version_id": "awv_001", "actor_id": "advisor_1"},
            "correlation_id": "corr-resume",
        },
        "compare": {
            "workspace_id": "aws_001",
            "body": {"workspace_version_id": "awv_001"},
            "correlation_id": "corr-compare",
        },
        "rationale": {
            "workspace_id": "aws_001",
            "body": {"requested_by": "advisor_1", "instruction": "Summarize impact."},
            "correlation_id": "corr-rationale",
        },
        "review_rationale": {
            "workspace_id": "aws_001",
            "body": {
                "run_id": "packrun_workspace_001",
                "action_type": "APPROVE",
                "reviewed_by": "advisor_1",
            },
            "correlation_id": "corr-review-rationale",
        },
    }
    assert saved_versions.json()["data"]["items"][0]["workspace_version_id"] == "awv_001"
    assert compare.json()["data"]["comparison"]["trade_delta_count"] == 2
    assert rationale.json()["data"]["run_id"] == "packrun_workspace_001"
