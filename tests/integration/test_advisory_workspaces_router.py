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
