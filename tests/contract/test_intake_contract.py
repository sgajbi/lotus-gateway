from fastapi.testclient import TestClient

from app.contracts.intake import EnvelopeResponse, IntakeBundleRequest, LookupResponse
from app.main import app


def test_intake_contract_shapes() -> None:
    request = IntakeBundleRequest(
        body={
            "sourceSystem": "workbench",
            "portfolios": [{"portfolio_id": "PF_1001", "base_currency": "USD"}],
        }
    )
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

    assert request.body["sourceSystem"] == "workbench"
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
    assert "fully assembled bundle payload" in bundle_operation["description"]
    assert "write-ingress handoff" in bundle_operation["description"]
    bundle_parameters = {
        parameter["name"]: parameter for parameter in bundle_operation["parameters"]
    }
    assert bundle_parameters["X-Idempotency-Key"]["description"]
    assert (
        "replay the original ingestion job safely"
        in bundle_parameters["X-Idempotency-Key"]["description"]
    )
    assert bundle_parameters["X-Idempotency-Key"]["schema"]["examples"] == ["bundle-idem-1001"]
    assert preview_operation["description"]
    assert "sample rows" in preview_operation["description"]
    assert "snake_case multipart contract" in preview_operation["description"]
    assert commit_operation["description"]
    assert "after preview" in commit_operation["description"]
    assert "allow_partial" in commit_operation["description"]
    assert portfolio_lookup_operation["description"]
    assert "selector-only" in portfolio_lookup_operation["description"]
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
    assert "lotus-core `client_id`" in portfolio_parameters["cif_id"]["description"]
    assert portfolio_parameters["cif_id"]["schema"]["examples"] == ["CIF_1001"]
    assert portfolio_parameters["booking_center"]["description"]
    assert (
        "lotus-core `booking_center_code`" in portfolio_parameters["booking_center"]["description"]
    )
    assert portfolio_parameters["booking_center"]["schema"]["examples"] == ["SG"]
    assert portfolio_parameters["q"]["description"]
    assert portfolio_parameters["q"]["schema"]["examples"] == ["Alpha"]
    assert portfolio_parameters["limit"]["description"]
    assert portfolio_parameters["limit"]["schema"]["examples"] == [100]
    assert instrument_parameters["limit"]["description"]
    assert instrument_parameters["limit"]["schema"]["default"] == 200
    assert instrument_parameters["product_type"]["description"]
    assert instrument_parameters["product_type"]["schema"]["examples"] == ["EQUITY"]
    assert instrument_parameters["q"]["description"]
    assert instrument_parameters["q"]["schema"]["examples"] == ["Apple"]
    assert currency_parameters["instrument_page_limit"]["description"]
    assert currency_parameters["instrument_page_limit"]["schema"]["examples"] == [500]
    assert currency_parameters["source"]["description"]
    assert currency_parameters["source"]["schema"]["examples"] == ["ALL"]
    assert currency_parameters["q"]["description"]
    assert currency_parameters["q"]["schema"]["examples"] == ["USD"]
    assert currency_parameters["limit"]["description"]
    assert currency_parameters["limit"]["schema"]["examples"] == [50]

    assert request_schema["properties"]["body"]["description"]
    assert request_schema["properties"]["body"]["examples"][0]["sourceSystem"] == "workbench"
    assert envelope_schema["properties"]["correlation_id"]["description"]
    assert envelope_schema["properties"]["contract_version"]["description"]
    assert envelope_schema["properties"]["contract_version"]["default"] == "v1"
    assert envelope_schema["properties"]["data"]["description"]
    assert envelope_schema["properties"]["data"]["examples"][0]["job_id"] == "ingest-42"
    assert lookup_item_schema["properties"]["id"]["description"]
    assert lookup_item_schema["properties"]["label"]["description"]
    assert lookup_response_schema["properties"]["correlation_id"]["description"]
    assert lookup_response_schema["properties"]["contract_version"]["description"]
    assert lookup_response_schema["properties"]["contract_version"]["default"] == "v1"
    assert lookup_response_schema["properties"]["items"]["description"]
    assert lookup_response_schema["properties"]["items"]["examples"][0][0]["id"] == "PF_1001"

    preview_body_ref = preview_operation["requestBody"]["content"]["multipart/form-data"]["schema"][
        "$ref"
    ]
    commit_body_ref = commit_operation["requestBody"]["content"]["multipart/form-data"]["schema"][
        "$ref"
    ]
    preview_body_schema = spec["components"]["schemas"][preview_body_ref.rsplit("/", 1)[-1]]
    commit_body_schema = spec["components"]["schemas"][commit_body_ref.rsplit("/", 1)[-1]]
    preview_entity_type_schema = preview_body_schema["properties"]["entityType"]
    preview_file_schema = preview_body_schema["properties"]["file"]
    preview_sample_size_schema = preview_body_schema["properties"]["sampleSize"]
    commit_entity_type_schema = commit_body_schema["properties"]["entityType"]
    commit_file_schema = commit_body_schema["properties"]["file"]
    commit_allow_partial_schema = commit_body_schema["properties"]["allowPartial"]

    assert preview_entity_type_schema["description"]
    assert preview_entity_type_schema["examples"] == ["transactions"]
    assert preview_file_schema["description"]
    assert preview_sample_size_schema["description"]
    assert preview_sample_size_schema["default"] == 20
    assert preview_sample_size_schema["minimum"] == 1
    assert preview_sample_size_schema["maximum"] == 100
    assert preview_sample_size_schema["examples"] == [20]
    assert commit_entity_type_schema["description"]
    assert commit_entity_type_schema["examples"] == ["transactions"]
    assert commit_file_schema["description"]
    assert commit_allow_partial_schema["description"]
    assert commit_allow_partial_schema["default"] is False
    assert commit_allow_partial_schema["examples"] == [False]
