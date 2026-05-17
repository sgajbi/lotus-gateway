from fastapi.testclient import TestClient

from app.main import app


class _FakeCoreSourceProductClient:
    calls: list[dict[str, object]] = []

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
        return 200, {
            "product_name": "ExternalOrderExecutionAcknowledgement",
            "product_version": "v1",
            "portfolio_id": portfolio_id,
            "client_id": "CIF_SG_000184",
            "mandate_id": "MANDATE_SG_001",
            "execution_intent_id": payload.get("execution_intent_id"),
            "order_reference_ids": payload.get("order_reference_ids", []),
            "acknowledgements": [],
            "data_quality_status": "MISSING",
            "supportability": {
                "state": "UNAVAILABLE",
                "reason": "EXTERNAL_OMS_SOURCE_NOT_INGESTED",
                "acknowledgement_count": 0,
                "missing_data_families": ["external_oms_order_execution_acknowledgement"],
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
            },
            "lineage": {
                "source_system": "external-bank-oms",
                "source_table": "not_ingested",
                "contract_version": ("rfc_042_external_order_execution_acknowledgement_v1"),
                "integration_status": "not_ingested",
                "runtime_posture": "fail_closed",
                "non_claims": (
                    "order_generation,venue_routing,best_execution,"
                    "oms_acknowledgement,fills,settlement,"
                    "execution_status_certification,autonomous_execution_action"
                ),
            },
        }


def test_source_product_router_preserves_core_execution_acknowledgement_payload(monkeypatch):
    fake_client = _FakeCoreSourceProductClient()
    monkeypatch.setattr(
        "app.routers.source_products._source_product_core_client",
        lambda: fake_client,
    )
    client = TestClient(app)

    response = client.post(
        (
            "/api/v1/source-products/portfolios/PB_SG_GLOBAL_BAL_001/"
            "external-order-execution-acknowledgement"
        ),
        json={
            "as_of_date": "2026-05-18",
            "tenant_id": "default",
            "mandate_id": "MANDATE_SG_001",
            "execution_intent_id": "exec-intent-001",
            "order_reference_ids": ["order-ref-001"],
        },
        headers={"X-Correlation-Id": "corr-source-product"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_name"] == "ExternalOrderExecutionAcknowledgement"
    assert payload["product_version"] == "v1"
    assert payload["supportability"]["state"] == "UNAVAILABLE"
    assert payload["supportability"]["reason"] == "EXTERNAL_OMS_SOURCE_NOT_INGESTED"
    assert payload["supportability"]["missing_data_families"] == [
        "external_oms_order_execution_acknowledgement"
    ]
    assert payload["supportability"]["blocked_capabilities"] == [
        "order_generation",
        "venue_routing",
        "best_execution",
        "oms_acknowledgement",
        "fills",
        "settlement",
        "execution_status_certification",
        "autonomous_execution",
    ]
    assert payload["acknowledgements"] == []
    assert payload["data_quality_status"] == "MISSING"
    assert payload["lineage"]["runtime_posture"] == "fail_closed"
    assert payload["lineage"]["integration_status"] == "not_ingested"

    assert fake_client.calls == [
        {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "payload": {
                "as_of_date": "2026-05-18",
                "tenant_id": "default",
                "mandate_id": "MANDATE_SG_001",
                "execution_intent_id": "exec-intent-001",
                "order_reference_ids": ["order-ref-001"],
            },
            "correlation_id": "corr-source-product",
        }
    ]


def test_source_product_router_maps_core_validation_error_without_local_execution_truth(
    monkeypatch,
):
    class _ValidationErrorClient:
        async def get_external_order_execution_acknowledgement(self, **_: object):
            return 422, {"detail": "invalid as_of_date"}

    monkeypatch.setattr(
        "app.routers.source_products._source_product_core_client",
        lambda: _ValidationErrorClient(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/source-products/portfolios/P1/external-order-execution-acknowledgement",
        json={"as_of_date": "not-a-date", "order_reference_ids": []},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["source_service"] == "lotus-core"
    assert detail["upstream_status"] == 422
    assert detail["error"] == {"detail": "invalid as_of_date"}
