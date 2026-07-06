import pytest
from fastapi import HTTPException

from app.services.source_product_execution_service import SourceProductExecutionService


class _CoreSourceProductClient:
    def __init__(self, status_code: int, payload: dict[str, object]) -> None:
        self._status_code = status_code
        self._payload = payload
        self.calls: list[dict[str, object]] = []

    async def get_external_order_execution_acknowledgement(
        self,
        *,
        portfolio_id: str,
        payload: dict[str, object],
        correlation_id: str,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append(
            {
                "portfolio_id": portfolio_id,
                "payload": payload,
                "correlation_id": correlation_id,
            }
        )
        return self._status_code, self._payload


def _source_product_payload() -> dict[str, object]:
    return {
        "product_name": "ExternalOrderExecutionAcknowledgement",
        "product_version": "v1",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "acknowledgements": [],
        "supportability": {
            "state": "UNAVAILABLE",
            "reason": "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
            "acknowledgement_count": 0,
            "missing_data_families": ["external_oms_order_execution_acknowledgement"],
            "blocked_capabilities": ["oms_acknowledgement"],
        },
        "lineage": {"runtime_posture": "fail_closed"},
    }


@pytest.mark.asyncio
async def test_source_product_execution_service_returns_core_owned_response() -> None:
    core_client = _CoreSourceProductClient(200, _source_product_payload())
    service = SourceProductExecutionService(lotus_core_query_client=core_client)

    response = await service.get_external_order_execution_acknowledgement(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        payload={"as_of_date": "2026-05-18"},
        correlation_id="corr-source-product",
    )

    assert response.product_name == "ExternalOrderExecutionAcknowledgement"
    assert response.product_version == "v1"
    assert response.supportability.state == "UNAVAILABLE"
    assert response.supportability.reason == "EXTERNAL_OMS_SOURCE_NOT_INGESTED"
    assert response.lineage == {"runtime_posture": "fail_closed"}
    assert core_client.calls == [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "payload": {"as_of_date": "2026-05-18"},
            "correlation_id": "corr-source-product",
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("upstream_status", "gateway_status"),
    [
        (400, 400),
        (422, 400),
        (404, 404),
        (500, 502),
    ],
)
async def test_source_product_execution_service_maps_core_errors(
    upstream_status: int,
    gateway_status: int,
) -> None:
    core_client = _CoreSourceProductClient(
        upstream_status,
        {
            "detail": "core error",
            "portfolio_id": "PB_SENSITIVE",
            "execution_intent_id": "exec-sensitive",
        },
    )
    service = SourceProductExecutionService(lotus_core_query_client=core_client)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_external_order_execution_acknowledgement(
            portfolio_id="P1",
            payload={"as_of_date": "not-a-date"},
            correlation_id="corr-error",
        )

    assert exc_info.value.status_code == gateway_status
    assert exc_info.value.detail == {
        "source_service": "lotus-core",
        "upstream_status": upstream_status,
        "error_code": "UPSTREAM_SERVICE_ERROR",
        "detail": "Upstream service request failed.",
    }
