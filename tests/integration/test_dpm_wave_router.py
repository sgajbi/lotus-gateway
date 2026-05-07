from fastapi.testclient import TestClient

from app.main import app


def test_dpm_wave_create_forwards_body_and_idempotency_key(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_create_wave(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["idempotency_key"] = idempotency_key
        captured["correlation_id"] = correlation_id
        return 201, {
            "wave": {"wave_id": "dwv_001", "state": "PREVIEWED"},
            "durable": True,
            "supportability": {
                "supportability_state": "ready",
                "reason": "wave_supportability_ready",
            },
        }

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.create_wave", _fake_create_wave)

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves",
        json={
            "idempotency_key": "wave-idem-1",
            "body": {
                "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
                "trigger_id": "manual-wave-20260503-001",
                "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            },
        },
        headers={"X-Correlation-Id": "corr-wave-router-create"},
    )

    assert response.status_code == 200
    assert captured == {
        "body": {
            "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
            "trigger_id": "manual-wave-20260503-001",
            "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
        },
        "idempotency_key": "wave-idem-1",
        "correlation_id": "corr-wave-router-create",
    }
    payload = response.json()
    assert payload["supportability"]["state"] == "ready"
    assert payload["data"]["wave"]["wave_id"] == "dwv_001"


def test_dpm_wave_list_passes_filters_without_reconstructing_state(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_list_waves(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {
            "items": [
                {
                    "wave_id": "dwv_001",
                    "wave_state": "HANDOFF_READY",
                    "supportability_state": "ready",
                }
            ],
            "limit": 25,
            "offset": 0,
            "returned_count": 1,
        }

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_waves", _fake_list_waves)

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/waves"
        "?state=HANDOFF_READY&supportability_state=ready&limit=25&offset=0",
        headers={"X-Correlation-Id": "corr-wave-router-list"},
    )

    assert response.status_code == 200
    assert captured == {
        "params": {
            "state": "HANDOFF_READY",
            "trigger_type": None,
            "as_of_date": None,
            "supportability_state": "ready",
            "limit": 25,
            "offset": 0,
        },
        "correlation_id": "corr-wave-router-list",
    }
    assert response.json()["data"]["items"][0]["wave_state"] == "HANDOFF_READY"


def test_dpm_wave_actions_preserve_manage_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_select_wave_item(self, wave_id, wave_item_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["wave_id"] = wave_id
        captured["wave_item_id"] = wave_item_id
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "wave": {
                "wave_id": wave_id,
                "state": "SIMULATED",
                "items": [
                    {
                        "wave_item_id": wave_item_id,
                        "selected_alternative_id": body["alternative_id"],
                        "proof_pack_id": "dpp_wave_001",
                    }
                ],
            },
            "supportability": {"supportability_state": "ready"},
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.select_wave_item",
        _fake_select_wave_item,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves/dwv_001/items/dwi_001/select",
        json={
            "body": {
                "alternative_id": "alt_001",
                "actor_id": "pm_sg_1",
                "reason_code": "PM_SELECTED",
                "generate_proof_pack": True,
            }
        },
        headers={"X-Correlation-Id": "corr-wave-router-select"},
    )

    assert response.status_code == 200
    assert captured == {
        "wave_id": "dwv_001",
        "wave_item_id": "dwi_001",
        "body": {
            "alternative_id": "alt_001",
            "actor_id": "pm_sg_1",
            "reason_code": "PM_SELECTED",
            "generate_proof_pack": True,
        },
        "correlation_id": "corr-wave-router-select",
    }
    assert response.json()["data"]["wave"]["items"][0]["proof_pack_id"] == "dpp_wave_001"


def test_dpm_wave_error_is_not_marked_ready(monkeypatch) -> None:
    async def _fake_get_wave(self, wave_id, correlation_id):  # noqa: ANN001
        _ = self, wave_id, correlation_id
        return 404, {"detail": "Wave dwv_missing was not found."}

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_wave", _fake_get_wave)

    client = TestClient(app)
    response = client.get("/api/v1/dpm/command-center/waves/dwv_missing")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "MANAGE_WAVE_UPSTREAM_ERROR"
    assert response.json()["detail"]["detail"] == "Wave dwv_missing was not found."
