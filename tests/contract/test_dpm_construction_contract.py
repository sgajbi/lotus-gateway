from fastapi.testclient import TestClient

from app.contracts.dpm_construction import DpmConstructionGatewayResponse
from app.main import app


def test_dpm_construction_gateway_response_contract_shape() -> None:
    response = DpmConstructionGatewayResponse(
        correlation_id="corr-1",
        upstream_status=200,
        supportability={
            "state": "READY",
            "reason_codes": ["REGIME_SCENARIO_PACK_READY"],
            "selected_alternative_id": "alt_regime_stress_aware",
        },
        data={
            "alternative_set_id": "cas_1",
            "status": "READY",
            "alternatives": [
                {
                    "alternative_id": "alt_regime_stress_aware",
                    "method": "REGIME_STRESS_AWARE",
                    "method_status": "READY",
                }
            ],
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0039"
    assert response.data["alternative_set_id"] == "cas_1"


def test_dpm_construction_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    expected_paths = [
        (
            "/api/v1/dpm/command-center/construction/alternative-sets/generate",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/construction/alternative-sets/{alternative_set_id}",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/construction/alternative-sets/{alternative_set_id}/selections",
            "post",
        ),
    ]

    for path, method in expected_paths:
        assert path in spec["paths"]
        operation = spec["paths"][path][method]
        assert operation["tags"] == ["DPM Command Center"]
        assert operation["summary"]
        assert "What:" in operation["description"]
        assert "When:" in operation["description"]
        assert "How:" in operation["description"]


def test_dpm_construction_openapi_models_are_described() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]

    for schema_name in [
        "DpmConstructionGenerateRequest",
        "DpmConstructionSelectionRequest",
        "DpmConstructionGatewayResponse",
        "DpmConstructionSupportability",
        "DpmConstructionErrorDetail",
    ]:
        schema = schemas[schema_name]
        for property_schema in schema["properties"].values():
            assert property_schema.get("description")

    assert schemas["DpmConstructionGenerateRequest"]["properties"]["body"]["examples"]
    assert schemas["DpmConstructionGatewayResponse"]["properties"]["data"]["description"]
    assert schemas["DpmConstructionSupportability"]["properties"]["state"]["examples"]
