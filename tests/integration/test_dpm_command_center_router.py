from fastapi.testclient import TestClient

from app.main import app


def test_dpm_command_center_outcome_review_create_preserves_manage_truth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_create_outcome_review(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "outcome_review_id": "or_1",
            "state": "READY",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "expected_snapshot_hash": "sha256:expected",
            "realized_snapshot_hash": "sha256:realized",
            "supportability": {
                "state": "SUPPORTED",
                "reason_codes": ["READY_FOR_REPORT_INPUT"],
                "blocked_actions": [],
            },
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.create_outcome_review",
        _fake_create_outcome_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/outcome-reviews",
        json={"body": {"rebalance_run_id": "rr_1", "proof_pack_id": "ppack_1"}},
        headers={"X-Correlation-Id": "corr-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured == {
        "body": {"rebalance_run_id": "rr_1", "proof_pack_id": "ppack_1"},
        "correlation_id": "corr-router-1",
    }
    assert payload["correlation_id"] == "corr-router-1"
    assert payload["source_service"] == "lotus-manage"
    assert payload["supportability"]["state"] == "SUPPORTED"
    assert payload["data"]["expected_snapshot_hash"] == "sha256:expected"
    assert payload["data"]["realized_snapshot_hash"] == "sha256:realized"


def test_dpm_command_center_outcome_review_list_passes_filters(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_list_outcome_reviews(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {
            "items": [{"outcome_review_id": "or_1", "state": "READY"}],
            "next_cursor": None,
            "supportability": {"state": "SUPPORTED"},
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_outcome_reviews",
        _fake_list_outcome_reviews,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/outcome-reviews"
        "?portfolio_id=PB_SG_GLOBAL_BAL_001&state=READY&limit=10",
        headers={"X-Correlation-Id": "corr-router-2"},
    )

    assert response.status_code == 200
    assert captured == {
        "params": {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "rebalance_run_id": None,
            "wave_id": None,
            "state": "READY",
            "limit": 10,
            "cursor": None,
        },
        "correlation_id": "corr-router-2",
    }
    assert response.json()["data"]["items"][0]["outcome_review_id"] == "or_1"


def test_dpm_command_center_outcome_review_error_is_not_marked_supported(monkeypatch) -> None:
    async def _fake_get_outcome_review(self, outcome_review_id, correlation_id):  # noqa: ANN001
        _ = self, outcome_review_id, correlation_id
        return 404, {"detail": "outcome review not found"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review",
        _fake_get_outcome_review,
    )

    client = TestClient(app)
    response = client.get("/api/v1/dpm/command-center/outcome-reviews/or_missing")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR"
    assert response.json()["detail"]["detail"] == "outcome review not found"


def test_dpm_command_center_outcome_review_ai_narrative_executes_lotus_ai(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["manage"] = {
            "outcome_review_id": outcome_review_id,
            "correlation_id": correlation_id,
        }
        return 200, _outcome_ai_evidence(outcome_review_id)

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        _ = self
        captured["ai"] = kwargs
        return 200, {
            "execution": {
                "status": "COMPLETED",
                "audit": {"workflow_pack_run_id": "packrun_or_1"},
                "result": {
                    "structured_output": {
                        "outcome_review_narrative_status": "REVIEW_REQUIRED",
                        "evidence_content_hash": "sha256:or_1-ai-evidence",
                    }
                },
            },
            "workflow_pack_run": {
                "run_id": "packrun_or_1",
                "workflow_authority_owner": "lotus-manage",
            },
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review_ai_evidence_input",
        _fake_get_outcome_review_ai_evidence_input,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/outcome-reviews/or_1/ai-narrative",
        json={"requested_outputs": ["pm_summary", "evidence_gaps"], "audience": ["pm"]},
        headers={"X-Correlation-Id": "corr-ai-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["manage"] == {
        "outcome_review_id": "or_1",
        "correlation_id": "corr-ai-router-1",
    }
    ai_call = captured["ai"]
    assert ai_call["pack_id"] == "outcome_review_narrative.pack"
    assert ai_call["correlation_id"] == "corr-ai-router-1"
    assert ai_call["task_request"]["caller"]["caller_app"] == "lotus-gateway"
    assert payload["source_service"] == "lotus-ai"
    assert payload["evidence_source_service"] == "lotus-manage"
    assert payload["ai_evidence_input"]["content_hash"] == "sha256:or_1-ai-evidence"
    assert payload["data"]["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def _outcome_ai_evidence(outcome_review_id: str) -> dict[str, object]:
    return {
        "contract_version": "1.0",
        "outcome_review_id": outcome_review_id,
        "outcome_review_content_hash": "sha256:outcome-review",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "proof_pack_id": "pp_1",
        "permitted_use": "Draft support-only PM, CIO, compliance, and operations narratives.",
        "forbidden_actions": [
            "place_orders",
            "approve_rebalance",
            "override_controls",
            "invent_missing_evidence",
            "score_portfolio_manager",
            "contact_client",
        ],
        "forbidden_fields_removed": [],
        "overall_outcome": "Implemented rebalance stayed inside expected bands.",
        "dimensions": [{"dimension": "cash", "state": "MATCHED"}],
        "source_refs": [],
        "evidence_ref": {
            "source_id": f"{outcome_review_id}:dpm_outcome_ai_evidence_input",
            "content_hash": f"sha256:{outcome_review_id}-ai-evidence",
        },
        "content_hash": f"sha256:{outcome_review_id}-ai-evidence",
    }
