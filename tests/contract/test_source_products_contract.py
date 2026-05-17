from fastapi.testclient import TestClient

from app.main import app


def test_external_execution_acknowledgement_source_product_openapi_contract() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    path = (
        "/api/v1/source-products/portfolios/{portfolio_id}/external-order-execution-acknowledgement"
    )
    assert path in spec["paths"]
    operation = spec["paths"][path]["post"]
    assert operation["summary"] == "Get External Order Execution Acknowledgement Supportability"
    assert "ExternalOrderExecutionAcknowledgement:v1" in operation["description"]
    assert "preserves the response shape" in operation["description"]
    assert "does not generate orders" in operation["description"]
    assert "fills or settlement" in operation["description"]

    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert parameters["portfolio_id"]["schema"]["examples"] == ["PB_SG_GLOBAL_BAL_001"]
    assert parameters["X-Correlation-Id"]["description"]


def test_external_execution_acknowledgement_source_product_schemas_are_documented() -> None:
    client = TestClient(app)
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    request_schema = schemas["ExternalOrderExecutionAcknowledgementRequest"]
    response_schema = schemas["ExternalOrderExecutionAcknowledgementResponse"]
    supportability_schema = schemas["ExternalOrderExecutionAcknowledgementSupportability"]

    assert request_schema["properties"]["as_of_date"]["description"]
    assert request_schema["properties"]["order_reference_ids"]["description"]
    assert response_schema["properties"]["product_name"]["examples"] == [
        "ExternalOrderExecutionAcknowledgement"
    ]
    assert response_schema["properties"]["acknowledgements"]["description"]
    assert response_schema["properties"]["lineage"]["description"]
    assert supportability_schema["properties"]["state"]["examples"] == ["UNAVAILABLE"]
    assert supportability_schema["properties"]["missing_data_families"]["description"]
    assert supportability_schema["properties"]["blocked_capabilities"]["description"]
