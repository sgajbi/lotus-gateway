from app.main import app
from tests.support.dpm_caller import governed_dpm_client


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

    client = governed_dpm_client(app)
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
        "EXTERNAL_ELIGIBLE_HEDGE_INSTRUMENTS_FAIL_CLOSED",
        "EXTERNAL_HEDGE_POLICY_FAIL_CLOSED",
        "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
        "EXTERNAL_ORDER_EXECUTION_ACKNOWLEDGEMENT_FAIL_CLOSED",
        "REGIME_SCENARIO_PACK_READY",
        "TARGET_METHOD_COMPARISON_AVAILABLE",
    ]
    currency_context = payload["data"]["alternatives"][0]["diagnostics"]["authority_context"][
        "currency_overlay_context"
    ]
    assert currency_context["external_hedge_policy_source_product_name"] == ("ExternalHedgePolicy")
    assert currency_context["external_hedge_policy_rule_count"] == 0
    assert currency_context["external_hedge_policy_rules"] == []
    assert currency_context["external_eligible_hedge_instrument_source_product_name"] == (
        "ExternalEligibleHedgeInstrument"
    )
    assert currency_context["external_eligible_hedge_instrument_source_product_version"] == "v1"
    assert currency_context["external_eligible_hedge_instrument_source_id"] == (
        "sha256:external-eligible-hedge-instrument"
    )
    assert currency_context["external_eligible_hedge_instrument_content_hash"] == (
        "sha256:external-eligible-hedge-instrument-content"
    )
    assert currency_context["external_eligible_hedge_instrument_count"] == 0
    assert currency_context["external_eligible_hedge_instruments"] == []
    assert currency_context["missing_data_families"] == [
        "external_hedge_policy",
        "external_eligible_hedge_instrument",
    ]
    assert "hedge_policy_approval" in currency_context["blocked_capabilities"]
    assert "eligible_instrument_selection" in currency_context["blocked_capabilities"]
    acknowledgement_context = payload["data"]["alternatives"][0]["diagnostics"][
        "authority_context"
    ]["execution_acknowledgement_context"]
    assert acknowledgement_context["source_product_name"] == (
        "ExternalOrderExecutionAcknowledgement"
    )
    assert acknowledgement_context["source_product_version"] == "v1"
    assert acknowledgement_context["acknowledgement_count"] == 0
    assert acknowledgement_context["acknowledgements"] == []
    assert (
        "external_oms_order_execution_acknowledgement"
        in (acknowledgement_context["missing_data_families"])
    )
    assert "best_execution" in acknowledgement_context["blocked_capabilities"]
    assert "oms_acknowledgement" in acknowledgement_context["blocked_capabilities"]
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

    client = governed_dpm_client(app)
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

    client = governed_dpm_client(app)
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
                    "authority_context": {
                        "currency_overlay_context": {
                            "supportability_status": "BLOCKED",
                            "source_system": "lotus-core",
                            "external_hedge_policy_source_product_name": ("ExternalHedgePolicy"),
                            "external_hedge_policy_source_product_version": "v1",
                            "external_hedge_policy_source_id": ("sha256:external-hedge-policy"),
                            "external_hedge_policy_content_hash": (
                                "sha256:external-hedge-policy-content"
                            ),
                            "external_hedge_policy_rule_count": 0,
                            "external_hedge_policy_rules": [],
                            "external_eligible_hedge_instrument_source_product_name": (
                                "ExternalEligibleHedgeInstrument"
                            ),
                            "external_eligible_hedge_instrument_source_product_version": "v1",
                            "external_eligible_hedge_instrument_source_id": (
                                "sha256:external-eligible-hedge-instrument"
                            ),
                            "external_eligible_hedge_instrument_content_hash": (
                                "sha256:external-eligible-hedge-instrument-content"
                            ),
                            "external_eligible_hedge_instrument_count": 0,
                            "external_eligible_hedge_instruments": [],
                            "missing_data_families": [
                                "external_hedge_policy",
                                "external_eligible_hedge_instrument",
                            ],
                            "blocked_capabilities": [
                                "hedge_policy_approval",
                                "eligible_instrument_selection",
                                "suitability_approval",
                                "product_recommendation",
                                "treasury_instruction",
                                "counterparty_selection",
                                "best_execution",
                                "oms_acknowledgement",
                                "fills",
                                "settlement",
                                "autonomous_treasury_action",
                            ],
                            "reason_codes": [
                                "EXTERNAL_HEDGE_POLICY_FAIL_CLOSED",
                                "EXTERNAL_ELIGIBLE_HEDGE_INSTRUMENTS_FAIL_CLOSED",
                            ],
                        },
                        "execution_acknowledgement_context": {
                            "supportability_status": "BLOCKED",
                            "source_system": "lotus-core",
                            "source_product_name": "ExternalOrderExecutionAcknowledgement",
                            "source_product_version": "v1",
                            "source_id": "sha256:external-order-execution-acknowledgement",
                            "content_hash": (
                                "sha256:external-order-execution-acknowledgement-content"
                            ),
                            "acknowledgement_count": 0,
                            "missing_data_families": [
                                "external_oms_order_execution_acknowledgement"
                            ],
                            "blocked_capabilities": [
                                "order_generation",
                                "venue_routing",
                                "best_execution",
                                "oms_acknowledgement",
                                "fills",
                                "settlement",
                                "execution_status_certification",
                                "autonomous_execution",
                            ],
                            "acknowledgements": [],
                            "reason_codes": [
                                "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
                                "EXTERNAL_ORDER_EXECUTION_ACKNOWLEDGEMENT_FAIL_CLOSED",
                            ],
                        },
                    },
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
