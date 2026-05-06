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
        "REGIME_SCENARIO_PACK_READY",
        "TARGET_METHOD_COMPARISON_AVAILABLE",
    ]
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
