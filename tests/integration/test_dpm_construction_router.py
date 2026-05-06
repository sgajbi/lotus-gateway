from fastapi.testclient import TestClient

from app.main import app


def test_dpm_construction_generate_preserves_manage_truth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_generate_construction_alternative_set(
        self,
        body,
        idempotency_key,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["idempotency_key"] = idempotency_key
        captured["correlation_id"] = correlation_id
        return 200, _construction_alternative_set()

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.generate_construction_alternative_set",
        _fake_generate_construction_alternative_set,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/construction/alternative-sets/generate",
        json={
            "idempotency_key": "idem-construction-router-1",
            "body": {"input_mode": "stateless", "methods": ["REGIME_STRESS_AWARE"]},
        },
        headers={"X-Correlation-Id": "corr-construction-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured == {
        "body": {"input_mode": "stateless", "methods": ["REGIME_STRESS_AWARE"]},
        "idempotency_key": "idem-construction-router-1",
        "correlation_id": "corr-construction-router-1",
    }
    assert payload["correlation_id"] == "corr-construction-router-1"
    assert payload["source_service"] == "lotus-manage"
    assert payload["supportability"]["state"] == "READY"
    assert payload["supportability"]["reason_codes"] == [
        "REGIME_SCENARIO_PACK_READY",
        "TARGET_METHOD_COMPARISON_AVAILABLE",
    ]
    assert payload["data"] == _construction_alternative_set()


def test_dpm_construction_get_uses_manage_identifier(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_construction_alternative_set(
        self,
        alternative_set_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["alternative_set_id"] = alternative_set_id
        captured["correlation_id"] = correlation_id
        return 200, _construction_alternative_set()

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_construction_alternative_set",
        _fake_get_construction_alternative_set,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/construction/alternative-sets/cas_1",
        headers={"X-Correlation-Id": "corr-construction-get-1"},
    )

    assert response.status_code == 200
    assert captured == {
        "alternative_set_id": "cas_1",
        "correlation_id": "corr-construction-get-1",
    }
    assert response.json()["data"]["alternative_set_id"] == "cas_1"


def test_dpm_construction_selection_preserves_manage_decision(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_select_construction_alternative(
        self,
        alternative_set_id,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["alternative_set_id"] = alternative_set_id
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "selection_id": "casel_1",
            "alternative_set_id": alternative_set_id,
            "alternative_id": body["alternative_id"],
            "actor_id": body["actor_id"],
            "reason_code": body["reason_code"],
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.select_construction_alternative",
        _fake_select_construction_alternative,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/construction/alternative-sets/cas_1/selections",
        json={
            "body": {
                "alternative_id": "alt_regime_stress_aware",
                "actor_id": "pm_sg_1",
                "reason_code": "PM_SELECTED_REGIME_AWARE",
            }
        },
        headers={"X-Correlation-Id": "corr-construction-select-1"},
    )

    assert response.status_code == 200
    assert captured == {
        "alternative_set_id": "cas_1",
        "body": {
            "alternative_id": "alt_regime_stress_aware",
            "actor_id": "pm_sg_1",
            "reason_code": "PM_SELECTED_REGIME_AWARE",
        },
        "correlation_id": "corr-construction-select-1",
    }
    payload = response.json()
    assert payload["supportability"]["selected_alternative_id"] == "alt_regime_stress_aware"
    assert payload["data"]["selection_id"] == "casel_1"


def _construction_alternative_set() -> dict[str, object]:
    return {
        "alternative_set_id": "cas_1",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "status": "READY",
        "alternatives": [
            {
                "alternative_id": "alt_regime_stress_aware",
                "method": "REGIME_STRESS_AWARE",
                "method_status": "READY",
                "objective_trace": [],
                "constraint_trace": [],
                "comparison_metrics": {"turnover_weight": "0.05"},
                "diagnostics": {
                    "method_plan": {
                        "reason_codes": ["TARGET_METHOD_COMPARISON_AVAILABLE"],
                    },
                    "enrichment_summary": {
                        "reason_codes": ["REGIME_SCENARIO_PACK_READY"],
                    },
                },
            }
        ],
    }
