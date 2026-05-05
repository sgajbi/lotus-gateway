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
