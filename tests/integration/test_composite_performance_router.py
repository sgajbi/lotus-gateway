from fastapi.testclient import TestClient

from app.main import app

CALLER_CONTEXT_HEADERS = {
    "X-Actor-Id": "advisor_1",
    "X-Caller-Application": "lotus-workbench",
    "X-Tenant-Id": "tenant-sg",
    "X-Region": "APAC",
    "X-Booking-Center-Code": "SG",
    "X-Role": "advisor",
    "X-Correlation-Id": "corr-composite-1",
}


def test_composite_twr_route_preserves_lotus_performance_payload(monkeypatch):
    async def _post_composite_twr(self, payload, correlation_id):  # noqa: ARG001
        assert correlation_id == "corr-composite-1"
        assert payload == {
            "calculation_id": "calc-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        }
        return 200, {
            "calculation_id": "calc-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "status": "READY",
            "methodology": "persisted_member_return_asset_weighted_twr_v1",
            "periods": [
                {
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "status": "READY",
                    "return_value": "0.012500000000",
                    "source_fingerprints": ["sha256:fact-1"],
                    "restatement_versions": ["v1"],
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_composite_twr",
        _post_composite_twr,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/performance/composites/twr",
        headers=CALLER_CONTEXT_HEADERS,
        json={
            "calculation_id": "calc-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["correlation_id"] == "corr-composite-1"
    assert body["contract_version"] == "composite-performance-gateway.v1"
    assert body["source_service"] == "lotus-performance"
    assert body["upstream_status"] == 200
    assert body["data"]["methodology"] == "persisted_member_return_asset_weighted_twr_v1"
    assert body["data"]["periods"][0]["source_fingerprints"] == ["sha256:fact-1"]


def test_composite_inspection_route_preserves_classified_artifacts(monkeypatch):
    async def _post_composite_inspection(self, payload, correlation_id):  # noqa: ARG001
        assert payload["inspection_id"] == "insp-1"
        return 200, {
            "inspection_id": "insp-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "status": "complete",
            "verdict": "supportable_with_warnings",
            "findings": [
                {
                    "code": "DEGRADED_PERIOD",
                    "severity": "warning",
                    "category": "member_return_fact_quality",
                    "owner_repo": "lotus-performance",
                    "summary": "One period is degraded.",
                    "recommended_action": "Review member fact lineage.",
                    "evidence": {"period": "2026-01"},
                }
            ],
            "artifacts": [
                {
                    "artifact_name": "member_inputs.csv",
                    "content_type": "text/csv",
                    "access_classification": "operator_only",
                    "artifact_content": "portfolio_id,return_value\nPB_SG_GLOBAL_BAL_001,0.0125\n",
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.post_composite_inspection",
        _post_composite_inspection,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/performance/composites/inspect",
        headers=CALLER_CONTEXT_HEADERS,
        json={
            "inspection_id": "insp-1",
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["verdict"] == "supportable_with_warnings"
    assert body["data"]["findings"][0]["owner_repo"] == "lotus-performance"
    assert body["data"]["artifacts"][0]["artifact_name"] == "member_inputs.csv"
    assert "artifact_content" in body["data"]["artifacts"][0]


def test_composite_routes_require_governed_caller_context():
    client = TestClient(app)

    response = client.post(
        "/api/v1/performance/composites/twr",
        json={
            "composite_id": "PB_GLOBAL_BALANCED_USD",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "missing_caller_context"
    assert detail["missing_headers"] == ["X-Actor-Id", "X-Tenant-Id", "X-Region"]


def test_composite_performance_openapi_contract_registered():
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    twr_route = spec["paths"]["/api/v1/performance/composites/twr"]["post"]
    inspect_route = spec["paths"]["/api/v1/performance/composites/inspect"]["post"]
    request_schema = spec["components"]["schemas"]["CompositePerformanceTwrRequest"]
    inspect_request_schema = spec["components"]["schemas"]["CompositePerformanceInspectionRequest"]
    response_schema = spec["components"]["schemas"]["CompositePerformanceGatewayResponse"]

    assert twr_route["summary"] == "Calculate Persisted Composite TWR"
    assert "does not calculate returns" in twr_route["description"]
    assert inspect_route["summary"] == "Inspect Composite Performance Evidence"
    assert "classified artifacts" in inspect_route["description"]
    assert request_schema["properties"]["composite_id"]["description"]
    assert request_schema["properties"]["period_start"]["examples"] == ["2026-01-01"]
    assert inspect_request_schema["properties"]["inspection_id"]["description"]
    assert response_schema["properties"]["data"]["description"]
    assert (
        "source-owned composite payload"
        in response_schema["properties"]["data"]["description"].lower()
    )
