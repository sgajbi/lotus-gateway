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
                "workbench_posture": "CANONICAL_WORKBENCH_PROOF_PASSED_RFC0026",
                "client_ready_publication": "BLOCKED",
            },
        }

    async def _fake_preparation_packets(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["preparation_packets"] = {"params": params, "correlation_id": correlation_id}
        return 200, {
            "items": [
                {
                    "packet_id": "prep_packet_PB_SG_GLOBAL_BAL_001",
                    "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                    "meeting_posture": "READY_WITH_REVIEW_ITEMS",
                    "policy_posture": "PENDING_REVIEW",
                    "client_ready_publication": "BLOCKED",
                }
            ],
            "total_count": 1,
        }

    async def _fake_supportability(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["supportability"] = {"params": params, "correlation_id": correlation_id}
        return 200, {
            "posture": "ADVISE_GATEWAY_WORKBENCH_CANONICAL_PROOF_SUPPORTED",
            "supportability": {
                "gateway_posture": "SUPPORTED_BY_LOTUS_GATEWAY_RFC0026",
                "workbench_posture": "CANONICAL_WORKBENCH_PROOF_PASSED_RFC0026",
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

    async def _fake_house_view(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["house_view"] = {"body": body, "correlation_id": correlation_id}
        return 200, {
            "product_name": "TacticalHouseViewAffectedCohort",
            "affected_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            "supportability": {"state": "READY"},
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
        "app.clients.advise_client.AdviseClient.list_advisor_cockpit_preparation_packets",
        _fake_preparation_packets,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.get_advisor_cockpit_supportability",
        _fake_supportability,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.acknowledge_advisor_cockpit_action",
        _fake_ack,
    )
    monkeypatch.setattr(
        "app.clients.advise_client.AdviseClient.evaluate_advisor_cockpit_house_view_cohort",
        _fake_house_view,
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
    preparation_packets_response = client.get(
        "/api/v1/advisor-cockpit/preparation-packets",
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "advisor_id": "advisor_sg_001",
            "role": "ADVISOR",
            "limit": "10",
        },
        headers={"X-Correlation-Id": "corr-cockpit-prep"},
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
    house_view_response = client.post(
        "/api/v1/advisor-cockpit/house-view-cohorts/evaluate",
        json={
            "body": {
                "tactical_view": {"tactical_view_id": "thv_2026_05_asia_duration"},
                "candidate_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            }
        },
        headers={"X-Correlation-Id": "corr-cockpit-house-view"},
    )

    assert list_response.status_code == 200
    assert snapshot_response.status_code == 200
    assert preparation_packets_response.status_code == 200
    assert supportability_response.status_code == 200
    assert acknowledgement_response.status_code == 200
    assert house_view_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["status"] == "PENDING_REVIEW"
    assert snapshot_response.json()["data"]["supportability"]["client_ready_publication"] == (
        "BLOCKED"
    )
    assert (
        preparation_packets_response.json()["data"]["items"][0]["client_ready_publication"]
        == "BLOCKED"
    )
    assert acknowledgement_response.json()["data"]["action_item"]["status"] == "PENDING_REVIEW"
    assert house_view_response.json()["data"]["product_name"] == "TacticalHouseViewAffectedCohort"
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
        "preparation_packets": {
            "params": {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "advisor_id": "advisor_sg_001",
                "role": "ADVISOR",
                "limit": 10,
            },
            "correlation_id": "corr-cockpit-prep",
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
        "house_view": {
            "body": {
                "tactical_view": {"tactical_view_id": "thv_2026_05_asia_duration"},
                "candidate_portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            },
            "correlation_id": "corr-cockpit-house-view",
        },
    }


def test_advisor_cockpit_openapi_documents_boundary_and_idempotency() -> None:
    schema = app.openapi()
    action_operation = schema["paths"]["/api/v1/advisor-cockpit/actions"]["get"]
    preparation_operation = schema["paths"]["/api/v1/advisor-cockpit/preparation-packets"]["get"]
    house_view_operation = schema["paths"]["/api/v1/advisor-cockpit/house-view-cohorts/evaluate"][
        "post"
    ]
    ack_operation = schema["paths"][
        "/api/v1/advisor-cockpit/actions/{action_item_id}/acknowledgements"
    ]["post"]

    assert "without reconstructing advisory semantics" in action_operation["description"]
    assert "without reconstructing preparation semantics" in preparation_operation["description"]
    assert "HOUSE_VIEW_IMPACT_REVIEW" in house_view_operation["description"]
    assert "does not discover candidate portfolios" in house_view_operation["description"]
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
