from fastapi.testclient import TestClient

from app.main import app


def test_advisor_cockpit_routes_forward_to_advise_without_rewriting(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_list(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["list"] = {"params": params, "correlation_id": correlation_id}
        return 200, {
            "items": [
                {
                    "action_item_id": "cockpit_action_001",
                    "status": "PENDING_REVIEW",
                    "priority": "HIGH",
                    "owner_role": "ADVISOR",
                }
            ],
            "total_count": 1,
        }

    async def _fake_snapshot(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["snapshot"] = {"params": params, "correlation_id": correlation_id}
        return 200, {
            "snapshot_id": "cockpit_snapshot_PB_SG_GLOBAL_BAL_001",
            "supportability": {
                "gateway_posture": "SUPPORTED_BY_LOTUS_GATEWAY_RFC0026",
                "workbench_posture": "MANDATORY_SUBSEQUENT_RFC0026_SLICE",
                "client_ready_publication": "BLOCKED",
            },
        }

    async def _fake_supportability(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["supportability"] = {"params": params, "correlation_id": correlation_id}
        return 200, {
            "posture": "ADVISE_API_SUPPORTED_DOWNSTREAM_GATED",
            "supportability": {
                "gateway_posture": "SUPPORTED_BY_LOTUS_GATEWAY_RFC0026",
                "workbench_posture": "MANDATORY_SUBSEQUENT_RFC0026_SLICE",
                "client_ready_publication": "BLOCKED",
            },
        }

    async def _fake_ack(
        self,
        action_item_id,
        body,
        params,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["acknowledge"] = {
            "action_item_id": action_item_id,
            "body": body,
            "params": params,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
        }
        return 200, {
            "action_item": {"action_item_id": action_item_id, "status": "PENDING_REVIEW"},
            "acknowledgement": {"acknowledged": True},
            "replayed": False,
        }

    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.list_advisor_cockpit_actions",
        _fake_list,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_advisor_cockpit_snapshot",
        _fake_snapshot,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_advisor_cockpit_supportability",
        _fake_supportability,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.acknowledge_advisor_cockpit_action",
        _fake_ack,
    )

    client = TestClient(app)
    list_response = client.get(
        "/api/v1/advisor-cockpit/actions",
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "advisor_id": "advisor_sg_001",
            "role": "ADVISOR",
            "limit": "25",
        },
        headers={"X-Correlation-Id": "corr-cockpit-list"},
    )
    snapshot_response = client.get(
        "/api/v1/advisor-cockpit/snapshot",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
        headers={"X-Correlation-Id": "corr-cockpit-snapshot"},
    )
    supportability_response = client.get(
        "/api/v1/advisor-cockpit/supportability",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
        headers={"X-Correlation-Id": "corr-cockpit-supportability"},
    )
    acknowledgement_response = client.post(
        "/api/v1/advisor-cockpit/actions/cockpit_action_001/acknowledgements",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
        json={
            "action_item_version": 1,
            "acknowledged_by": "advisor_sg_001",
            "acknowledgement_note": "Reviewed pending policy action.",
        },
        headers={
            "Idempotency-Key": "idem-cockpit-ack",
            "X-Correlation-Id": "corr-cockpit-ack",
        },
    )

    assert list_response.status_code == 200
    assert snapshot_response.status_code == 200
    assert supportability_response.status_code == 200
    assert acknowledgement_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["status"] == "PENDING_REVIEW"
    assert snapshot_response.json()["data"]["supportability"]["client_ready_publication"] == (
        "BLOCKED"
    )
    assert acknowledgement_response.json()["data"]["action_item"]["status"] == "PENDING_REVIEW"
    assert captured == {
        "list": {
            "params": {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "advisor_id": "advisor_sg_001",
                "role": "ADVISOR",
                "limit": 25,
            },
            "correlation_id": "corr-cockpit-list",
        },
        "snapshot": {
            "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
            "correlation_id": "corr-cockpit-snapshot",
        },
        "supportability": {
            "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
            "correlation_id": "corr-cockpit-supportability",
        },
        "acknowledge": {
            "action_item_id": "cockpit_action_001",
            "body": {
                "action_item_version": 1,
                "acknowledged_by": "advisor_sg_001",
                "acknowledgement_note": "Reviewed pending policy action.",
            },
            "params": {"portfolio_id": "PB_SG_GLOBAL_BAL_001", "role": "ADVISOR"},
            "idempotency_key": "idem-cockpit-ack",
            "correlation_id": "corr-cockpit-ack",
        },
    }


def test_advisor_cockpit_openapi_documents_boundary_and_idempotency() -> None:
    schema = app.openapi()
    action_operation = schema["paths"]["/api/v1/advisor-cockpit/actions"]["get"]
    ack_operation = schema["paths"][
        "/api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements"
    ]["post"]

    assert "without reconstructing advisory semantics" in action_operation["description"]
    assert "does not clear blocking policy" in ack_operation["description"]
    assert ack_operation["responses"]["409"]["description"] == (
        "lotus-advise rejected a conflicting acknowledgement idempotency key."
    )
    assert any(
        parameter["name"] == "Idempotency-Key"
        and parameter["in"] == "header"
        and parameter["required"] is True
        for parameter in ack_operation["parameters"]
    )
