import pytest
from fastapi import HTTPException

from app.services.dpm_construction_service import DpmConstructionService


class _FakeDpmClient:
    def __init__(self, result: tuple[int, dict]):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def generate_construction_alternative_set(
        self,
        body,
        idempotency_key,
        correlation_id,
    ):  # noqa: ANN001
        self.calls.append(
            {
                "method": "construction_generate",
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_construction_alternative_set(self, alternative_set_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "construction_get",
                "alternative_set_id": alternative_set_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def select_construction_alternative(
        self,
        alternative_set_id,
        body,
        correlation_id,
    ):  # noqa: ANN001
        self.calls.append(
            {
                "method": "construction_select",
                "alternative_set_id": alternative_set_id,
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result


@pytest.mark.asyncio
async def test_dpm_construction_preserves_manage_alternative_set_payload() -> None:
    manage_payload = _construction_alternative_set()
    client = _FakeDpmClient((200, manage_payload))
    service = DpmConstructionService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.generate_alternative_set(
        body={"input_mode": "stateless", "methods": ["REGIME_STRESS_AWARE"]},
        idempotency_key="idem-construction-1",
        correlation_id="corr-construction-1",
    )

    assert response.correlation_id == "corr-construction-1"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.supportability.authority == "lotus-manage:RFC-0039"
    assert response.supportability.state == "READY"
    assert response.supportability.reason_codes == [
        "EXTERNAL_ELIGIBLE_HEDGE_INSTRUMENTS_FAIL_CLOSED",
        "EXTERNAL_HEDGE_POLICY_FAIL_CLOSED",
        "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
        "EXTERNAL_ORDER_EXECUTION_ACKNOWLEDGEMENT_FAIL_CLOSED",
        "REGIME_SCENARIO_PACK_READY",
        "TARGET_METHOD_COMPARISON_AVAILABLE",
    ]
    currency_context = response.data["alternatives"][0]["diagnostics"]["authority_context"][
        "currency_overlay_context"
    ]
    assert currency_context["external_hedge_policy_source_product_name"] == ("ExternalHedgePolicy")
    assert currency_context["external_hedge_policy_source_product_version"] == "v1"
    assert currency_context["external_hedge_policy_source_id"] == ("sha256:external-hedge-policy")
    assert currency_context["external_hedge_policy_content_hash"] == (
        "sha256:external-hedge-policy-content"
    )
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
    acknowledgement_context = response.data["alternatives"][0]["diagnostics"]["authority_context"][
        "execution_acknowledgement_context"
    ]
    assert acknowledgement_context["source_product_name"] == (
        "ExternalOrderExecutionAcknowledgement"
    )
    assert acknowledgement_context["source_product_version"] == "v1"
    assert acknowledgement_context["source_id"] == (
        "sha256:external-order-execution-acknowledgement"
    )
    assert acknowledgement_context["content_hash"] == (
        "sha256:external-order-execution-acknowledgement-content"
    )
    assert acknowledgement_context["acknowledgement_count"] == 0
    assert acknowledgement_context["acknowledgements"] == []
    assert (
        "external_oms_order_execution_acknowledgement"
        in (acknowledgement_context["missing_data_families"])
    )
    assert "oms_acknowledgement" in acknowledgement_context["blocked_capabilities"]
    assert "fills" in acknowledgement_context["blocked_capabilities"]
    assert "settlement" in acknowledgement_context["blocked_capabilities"]
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "construction_generate",
            "body": {"input_mode": "stateless", "methods": ["REGIME_STRESS_AWARE"]},
            "idempotency_key": "idem-construction-1",
            "correlation_id": "corr-construction-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_construction_retrieves_manage_alternative_set_without_mutation() -> None:
    manage_payload = _construction_alternative_set()
    client = _FakeDpmClient((200, manage_payload))
    service = DpmConstructionService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_alternative_set(
        alternative_set_id="cas_1",
        correlation_id="corr-get-1",
    )

    assert response.data == manage_payload
    assert response.supportability.state == "READY"
    assert client.calls == [
        {
            "method": "construction_get",
            "alternative_set_id": "cas_1",
            "correlation_id": "corr-get-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_construction_selection_preserves_manage_decision() -> None:
    client = _FakeDpmClient(
        (
            200,
            {
                "selection_id": "casel_1",
                "alternative_set_id": "cas_1",
                "alternative_id": "alt_regime_stress_aware",
                "actor_id": "pm_sg_1",
                "reason_code": "PM_SELECTED_REGIME_AWARE",
            },
        )
    )
    service = DpmConstructionService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.select_alternative(
        alternative_set_id="cas_1",
        body={
            "alternative_id": "alt_regime_stress_aware",
            "actor_id": "pm_sg_1",
            "reason_code": "PM_SELECTED_REGIME_AWARE",
        },
        correlation_id="corr-select-1",
    )

    assert response.supportability.state == "UNKNOWN"
    assert response.supportability.selected_alternative_id == "alt_regime_stress_aware"
    assert response.data["selection_id"] == "casel_1"
    assert client.calls == [
        {
            "method": "construction_select",
            "alternative_set_id": "cas_1",
            "body": {
                "alternative_id": "alt_regime_stress_aware",
                "actor_id": "pm_sg_1",
                "reason_code": "PM_SELECTED_REGIME_AWARE",
            },
            "correlation_id": "corr-select-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_construction_forwards_manage_errors_as_product_safe_detail() -> None:
    client = _FakeDpmClient((409, {"detail": "CONSTRUCTION_IDEMPOTENCY_KEY_CONFLICT"}))
    service = DpmConstructionService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_alternative_set(
            body={"input_mode": "stateless"},
            idempotency_key="idem-conflict",
            correlation_id="corr-conflict",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 409,
        "error_code": "MANAGE_CONSTRUCTION_UPSTREAM_ERROR",
        "detail": "CONSTRUCTION_IDEMPOTENCY_KEY_CONFLICT",
    }


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
