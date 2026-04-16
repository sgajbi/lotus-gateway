from fastapi.testclient import TestClient

from app.contracts.intake import EnvelopeResponse, LookupResponse
from app.main import app


def test_intake_contract_shapes() -> None:
    envelope = EnvelopeResponse(
        correlation_id="corr-intake-1",
        contract_version="v1",
        data={"message": "queued"},
    )
    lookups = LookupResponse(
        correlation_id="corr-intake-2",
        contract_version="v1",
        items=[{"id": "PF_1001", "label": "PF_1001 | Alpha Growth"}],
    )

    assert envelope.data["message"] == "queued"
    assert lookups.items[0].id == "PF_1001"
    assert lookups.items[0].label == "PF_1001 | Alpha Growth"


def test_intake_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    assert "/api/v1/intake/portfolio-bundle" in spec["paths"]
    assert "/api/v1/intake/uploads/preview" in spec["paths"]
    assert "/api/v1/intake/uploads/commit" in spec["paths"]
    assert "/api/v1/lookups/portfolios" in spec["paths"]
    assert "/api/v1/lookups/instruments" in spec["paths"]
    assert "/api/v1/lookups/currencies" in spec["paths"]

    bundle_operation = spec["paths"]["/api/v1/intake/portfolio-bundle"]["post"]
    preview_operation = spec["paths"]["/api/v1/intake/uploads/preview"]["post"]
    commit_operation = spec["paths"]["/api/v1/intake/uploads/commit"]["post"]
    portfolio_lookup_operation = spec["paths"]["/api/v1/lookups/portfolios"]["get"]
    instrument_lookup_operation = spec["paths"]["/api/v1/lookups/instruments"]["get"]
    currency_lookup_operation = spec["paths"]["/api/v1/lookups/currencies"]["get"]

    request_schema = spec["components"]["schemas"]["IntakeBundleRequest"]
    envelope_schema = spec["components"]["schemas"]["EnvelopeResponse"]
    lookup_item_schema = spec["components"]["schemas"]["LookupItem"]
    lookup_response_schema = spec["components"]["schemas"]["LookupResponse"]

    assert bundle_operation["description"]
    assert preview_operation["description"]
    assert commit_operation["description"]
    assert portfolio_lookup_operation["description"]
    assert instrument_lookup_operation["description"]
    assert currency_lookup_operation["description"]

    portfolio_parameters = {
        parameter["name"]: parameter for parameter in portfolio_lookup_operation["parameters"]
    }
    instrument_parameters = {
        parameter["name"]: parameter for parameter in instrument_lookup_operation["parameters"]
    }
    currency_parameters = {
        parameter["name"]: parameter for parameter in currency_lookup_operation["parameters"]
    }

    assert portfolio_parameters["cif_id"]["description"]
    assert portfolio_parameters["booking_center"]["description"]
    assert portfolio_parameters["q"]["description"]
    assert portfolio_parameters["limit"]["description"]
    assert instrument_parameters["limit"]["description"]
    assert instrument_parameters["product_type"]["description"]
    assert instrument_parameters["q"]["description"]
    assert currency_parameters["instrument_page_limit"]["description"]
    assert currency_parameters["source"]["description"]
    assert currency_parameters["q"]["description"]
    assert currency_parameters["limit"]["description"]

    assert request_schema["properties"]["body"]["description"]
    assert envelope_schema["properties"]["correlation_id"]["description"]
    assert envelope_schema["properties"]["contract_version"]["description"]
    assert envelope_schema["properties"]["data"]["description"]
    assert lookup_item_schema["properties"]["id"]["description"]
    assert lookup_item_schema["properties"]["label"]["description"]
    assert lookup_response_schema["properties"]["correlation_id"]["description"]
    assert lookup_response_schema["properties"]["contract_version"]["description"]
    assert lookup_response_schema["properties"]["items"]["description"]
