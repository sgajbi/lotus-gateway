import pytest
from fastapi import HTTPException

from app.services.dpm_wave_service import DpmWaveService


class _FakeDpmClient:
    def __init__(self, result: tuple[int, dict]):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def create_wave(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "create_wave",
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def simulate_wave(self, wave_id, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "simulate_wave",
                "wave_id": wave_id,
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_wave_supportability(self, wave_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "get_wave_supportability",
                "wave_id": wave_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_manage_wave_truth_and_supportability() -> None:
    manage_payload = {
        "wave": {
            "wave_id": "dwv_001",
            "state": "HANDOFF_READY",
            "aggregate_metrics": {"item_count": 2, "ready_item_count": 2},
            "items": [
                {
                    "wave_item_id": "dwi_001",
                    "state": "HANDOFF_READY",
                    "proof_pack_id": "dpp_wave_001",
                }
            ],
        },
        "durable": True,
        "supportability": {
            "supportability_state": "ready",
            "reason": "wave_supportability_ready",
            "wave_id": "dwv_001",
            "wave_state": "HANDOFF_READY",
            "item_count": 2,
            "issues": [],
        },
    }
    client = _FakeDpmClient((201, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.create_wave(
        body={"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
        idempotency_key="wave-idem-1",
        correlation_id="corr-wave-create",
    )

    assert response.correlation_id == "corr-wave-create"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 201
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.supportability.state == "ready"
    assert response.supportability.reason_codes == ["wave_supportability_ready"]
    assert response.supportability.wave_id == "dwv_001"
    assert response.supportability.wave_state == "HANDOFF_READY"
    assert response.supportability.item_count == 2
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "create_wave",
            "body": {"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
            "idempotency_key": "wave-idem-1",
            "correlation_id": "corr-wave-create",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_forwards_simulation_without_local_reconstruction() -> None:
    manage_payload = {
        "wave": {
            "wave_id": "dwv_001",
            "state": "PARTIALLY_SIMULATED",
            "items": [{"wave_item_id": "dwi_001", "state": "SIMULATION_BLOCKED"}],
        },
        "supportability": {
            "supportability_state": "degraded",
            "reason": "wave_degraded_items",
            "issues": [{"support_ref": "wave:dwv_001:item:1"}],
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.simulate_wave(
        wave_id="dwv_001",
        body={"actor_id": "pm_sg_1", "item_inputs": []},
        correlation_id="corr-wave-simulate",
    )

    assert response.supportability.state == "degraded"
    assert response.supportability.reason_codes == ["wave_degraded_items"]
    assert response.supportability.issue_count == 1
    assert response.data["wave"] == manage_payload["wave"]
    assert client.calls == [
        {
            "method": "simulate_wave",
            "wave_id": "dwv_001",
            "body": {"actor_id": "pm_sg_1", "item_inputs": []},
            "correlation_id": "corr-wave-simulate",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_manage_errors_are_product_safe() -> None:
    client = _FakeDpmClient(
        (
            422,
            {
                "detail": {
                    "code": "DPM_WAVE_INVALID_TRANSITION",
                    "message": "Wave dwv_001 cannot be approved from state DRAFT.",
                }
            },
        )
    )
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_wave_supportability(
            wave_id="dwv_001",
            correlation_id="corr-wave-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 422,
        "error_code": "MANAGE_WAVE_UPSTREAM_ERROR",
        "detail": (
            "DPM_WAVE_INVALID_TRANSITION: Wave dwv_001 cannot be approved from state DRAFT."
        ),
    }
