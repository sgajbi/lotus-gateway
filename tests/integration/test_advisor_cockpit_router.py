from fastapi.testclient import TestClient

from app.main import app


def _caller_headers(
    *,
    capabilities: str = (
        "advisory.advisor_cockpit.read,advisory.advisor_cockpit.acknowledge"
    ),
    role: str = "ADVISOR",
    portfolio_id: str | None = "PB_SG_GLOBAL_BAL_001",
) -> dict[str, str]:
    headers = {
        "X-Actor-Id": "advisor_sg_001",
        "X-Caller-Application": "lotus-workbench",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SG",
        "X-Legal-Entity-Code": "SGPB",
        "X-Role": role,
        "X-Caller-Capabilities": capabilities,
        "X-Principal-Status": "ACTIVE",
        "X-Authorized-Advisor-Id": "advisor_sg_001",
    }
    if portfolio_id is not None:
        headers["X-Authorized-Portfolio-Id"] = portfolio_id
    return headers


def _expected_upstream_headers(*, capability: str) -> dict[str, str]:
    return {
        "X-Actor-Id": "advisor_sg_001",
        "X-Role": "ADVISOR",
        "X-Tenant-Id": "tenant-sg",
        "X-Legal-Entity-Code": "SGPB",
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": capability,
        "X-Principal-Status": "ACTIVE",
        "X-Authorized-Advisor-Id": "advisor_sg_001",
        "X-Authorized-Portfolio-Id": "PB_SG_GLOBAL_BAL_001",
    }


def test_advisor_cockpit_routes_forward_to_advise_without_rewriting(monkeypatch):
    captured: dict[str, object] = {}

    async def _fake_list(self, params, caller_headers, correlation_id):  # noqa: ANN001
        _ = self
        captured["list"] = {
            "params": params,
            "caller_headers": caller_headers,
            "correlation_id": correlation_id,
        }
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

    async def _fake_snapshot(self, params, caller_headers, correlation_id):  # noqa: ANN001
        _ = self
        captured["snapshot"] = {
            "params": params,
            "caller_headers": caller_headers,
            "correlation_id": correlation_id,
        }
        return 200, {
            "snapshot_id": "cockpit_snapshot_PB_SG_GLOBAL_BAL_001",
            "supportability": {
                "gateway_posture": "SUPPORTED_BY_LOTUS_GATEWAY_RFC0026",
                "workbench_posture": "CANONICAL_WORKBENCH_PROOF_PASSED_RFC0026",
                "client_ready_publication": "BLOCKED",
            },
        }

    async def _fake_get_action(
        self, action_item_id, params, caller_headers, correlation_id  # noqa: ANN001
    ):
        _ = self
        captured["get_action"] = {
            "action_item_id": action_item_id,
            "params": params,
            "caller_headers": caller_headers,
            "correlation_id": correlation_id,
        }
        return 200, {
            "action_item_id": action_item_id,
            "status": "PENDING_REVIEW",
            "priority": "HIGH",
            "owner_role": "ADVISOR",
        }

    async def _fake_preparation_packets(
        self, params, caller_headers, correlation_id  # noqa: ANN001
    ):
        _ = self
        captured["preparation_packets"] = {
            "params": params,
            "caller_headers": caller_headers,
            "correlation_id": correlation_id,
        }
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

    async def _fake_supportability(
        self, params, caller_headers, correlation_id  # noqa: ANN001
    ):
        _ = self
        captured["supportability"] = {
            "params": params,
            "caller_headers": caller_headers,
            "correlation_id": correlation_id,
        }
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
        caller_headers,
        idempotency_key,
        correlation_id,  # noqa: ANN001
    ):
        _ = self
        captured["acknowledge"] = {
            "action_item_id": action_item_id,
            "body": body,
            "params": params,
            "caller_headers": caller_headers,
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
        captured["house_view"] = {
            "body": body,
            "correlation_id": correlation_id,
        }
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
        "app.clients.advise_client.AdviseClient.get_advisor_cockpit_action",
        _fake_get_action,
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
            "limit": "25",
        },
        headers={**_caller_headers(), "X-Correlation-Id": "corr-cockpit-list"},
    )
    snapshot_response = client.get(
        "/api/v1/advisor-cockpit/snapshot",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
        headers={**_caller_headers(), "X-Correlation-Id": "corr-cockpit-snapshot"},
    )
    action_response = client.get(
        "/api/v1/advisor-cockpit/actions/cockpit_action_001",
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        },
        headers={**_caller_headers(), "X-Correlation-Id": "corr-cockpit-get-action"},
    )
    preparation_packets_response = client.get(
        "/api/v1/advisor-cockpit/preparation-packets",
        params={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "limit": "10",
        },
        headers={**_caller_headers(), "X-Correlation-Id": "corr-cockpit-prep"},
    )
    supportability_response = client.get(
        "/api/v1/advisor-cockpit/supportability",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
        headers={**_caller_headers(), "X-Correlation-Id": "corr-cockpit-supportability"},
    )
    acknowledgement_response = client.post(
        "/api/v1/advisor-cockpit/actions/cockpit_action_001/acknowledgements",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
        json={
            "action_item_version": 1,
            "acknowledgement_note": "Reviewed pending policy action.",
        },
        headers={
            "Idempotency-Key": "idem-cockpit-ack",
            "X-Correlation-Id": "corr-cockpit-ack",
            **_caller_headers(),
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
        headers={
            "X-Correlation-Id": "corr-cockpit-house-view",
        },
    )

    assert list_response.status_code == 200
    assert snapshot_response.status_code == 200
    assert action_response.status_code == 200
    assert preparation_packets_response.status_code == 200
    assert supportability_response.status_code == 200
    assert acknowledgement_response.status_code == 200
    assert house_view_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["status"] == "PENDING_REVIEW"
    assert action_response.json()["data"]["action_item_id"] == "cockpit_action_001"
    assert snapshot_response.json()["data"]["supportability"]["client_ready_publication"] == (
        "BLOCKED"
    )
    assert (
        preparation_packets_response.json()["data"]["items"][0]["client_ready_publication"]
        == "BLOCKED"
    )
    assert acknowledgement_response.json()["data"]["action_item"]["status"] == "PENDING_REVIEW"
    assert house_view_response.json()["data"]["product_name"] == "TacticalHouseViewAffectedCohort"
    expected_advisor_headers = _expected_upstream_headers(
        capability=(
            "advisory.advisor_cockpit.acknowledge,advisory.advisor_cockpit.read"
        )
    )
    for operation in (
        "list",
        "snapshot",
        "get_action",
        "preparation_packets",
        "supportability",
        "acknowledge",
    ):
        assert captured[operation]["caller_headers"] == expected_advisor_headers  # type: ignore[index]

    assert captured["list"]["params"] == {  # type: ignore[index]
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "limit": 25,
    }
    assert captured["snapshot"]["params"] == {  # type: ignore[index]
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
    }
    assert captured["get_action"]["action_item_id"] == "cockpit_action_001"  # type: ignore[index]
    assert captured["preparation_packets"]["params"] == {  # type: ignore[index]
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "limit": 10,
    }
    assert captured["acknowledge"]["body"] == {  # type: ignore[index]
        "action_item_version": 1,
        "acknowledged_by": "advisor_sg_001",
        "acknowledgement_note": "Reviewed pending policy action.",
    }
    assert captured["house_view"]["correlation_id"] == "corr-cockpit-house-view"  # type: ignore[index]


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
    assert "derived from trusted caller context" in action_operation["description"]
    assert "HOUSE_VIEW_IMPACT_REVIEW" in house_view_operation["description"]
    assert "does not discover candidate portfolios" in house_view_operation["description"]
    assert "does not clear blocking policy" in ack_operation["description"]
    assert "acknowledging actor is derived from trusted caller context" in ack_operation[
        "description"
    ]
    assert not any(
        parameter["name"] in {"advisor_id", "role"}
        and parameter["in"] == "query"
        for parameter in action_operation["parameters"]
    )
    assert {
        parameter["name"]
        for parameter in action_operation["parameters"]
        if parameter["in"] == "header"
    } >= {
        "X-Actor-Id",
        "X-Tenant-Id",
        "X-Region",
        "X-Booking-Center-Code",
        "X-Legal-Entity-Code",
        "X-Role",
        "X-Caller-Capabilities",
        "X-Principal-Status",
        "X-Authorized-Advisor-Id",
        "X-Authorized-Portfolio-Id",
    }
    assert ack_operation["responses"]["409"]["description"] == (
        "lotus-advise rejected a conflicting acknowledgement idempotency key."
    )
    assert any(
        parameter["name"] == "Idempotency-Key"
        and parameter["in"] == "header"
        and parameter["required"] is True
        for parameter in ack_operation["parameters"]
    )

    acknowledge_schema = schema["components"]["schemas"]["AdvisorCockpitAcknowledgeRequest"]
    assert "acknowledged_by" not in acknowledge_schema["properties"]
    assert acknowledge_schema["additionalProperties"] is False


def test_advisor_cockpit_rejects_browser_selected_authority() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/advisor-cockpit/actions",
        params={"advisor_id": "another_advisor", "role": "DESK_HEAD"},
        headers=_caller_headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "advisor_cockpit_authority_query_not_supported"
    )


def test_advisor_cockpit_fails_closed_without_trusted_context_or_capability() -> None:
    client = TestClient(app)

    missing_context = client.get("/api/v1/advisor-cockpit/actions")
    missing_capability = client.get(
        "/api/v1/advisor-cockpit/actions",
        headers=_caller_headers(capabilities="portfolio.read"),
    )

    assert missing_context.status_code == 400
    assert missing_context.json()["detail"]["code"] == (
        "advisor_cockpit_caller_context_missing"
    )
    assert missing_capability.status_code == 403
    assert missing_capability.json()["detail"]["code"] == "advisor_cockpit_access_denied"


def test_advisor_cockpit_rejects_cross_portfolio_access_before_upstream_call() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/advisor-cockpit/actions",
        params={"portfolio_id": "PB_NOT_ENTITLED"},
        headers=_caller_headers(),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "advisor_cockpit_portfolio_access_denied"
    )


def test_advisor_cockpit_action_lookup_requires_entitled_portfolio() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/advisor-cockpit/actions/cockpit_action_001",
        headers=_caller_headers(),
    )

    assert response.status_code == 422


def test_advisor_cockpit_acknowledgement_rejects_body_actor_override() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/advisor-cockpit/actions/cockpit_action_001/acknowledgements",
        params={"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
        headers={**_caller_headers(), "Idempotency-Key": "idem-actor-override"},
        json={
            "action_item_version": 1,
            "acknowledged_by": "another_advisor",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_tactical_house_view_route_does_not_claim_cockpit_authority() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/advisor-cockpit/house-view-cohorts/evaluate"
    ]["post"]

    assert not any(
        parameter["in"] == "header" and "Capability" in parameter["name"]
        for parameter in operation.get("parameters", [])
    )
