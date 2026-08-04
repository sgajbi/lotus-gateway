from fastapi.testclient import TestClient

from app.contracts.dpm_proof_packs import (
    DpmProofPackGatewayResponse,
    DpmProofPackMemoGatewayResponse,
)
from app.main import app
from tests.support.lotus_ai_workflow_pack import lotus_ai_workflow_pack_execution_v1


def test_dpm_proof_pack_gateway_response_contract_shape() -> None:
    response = DpmProofPackGatewayResponse(
        correlation_id="corr-1",
        upstream_status=200,
        supportability={
            "state": "READY",
            "reason_codes": ["PROOF_PACK_READY"],
            "proof_pack_id": "dpp_rr_001",
            "section_state_counts": {"READY": 2},
            "content_hash": "sha256:proof-pack",
            "markdown_available": True,
        },
        data={
            "proof_pack": {
                "proof_pack_id": "dpp_rr_001",
                "status": "READY",
                "content_hash": "sha256:proof-pack",
            }
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0040"
    assert response.supportability.proof_pack_id == "dpp_rr_001"
    assert response.data["proof_pack"]["content_hash"] == "sha256:proof-pack"


def test_dpm_proof_pack_pm_memo_gateway_response_contract_shape() -> None:
    response = DpmProofPackMemoGatewayResponse(
        correlation_id="corr-proof-pack-memo-1",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={
            "state": "SUPPORTED",
            "reason_codes": ["AI_EVIDENCE_INPUT_READY"],
            "proof_pack_id": "dpp_rr_001",
            "ai_evidence_input_available": True,
        },
        ai_evidence_input={
            "proof_pack_id": "dpp_rr_001",
            "content_hash": "sha256:ai-evidence",
        },
        memo_request={"requested_outputs": ["pm_memo"], "audience": ["portfolio_manager"]},
        data=lotus_ai_workflow_pack_execution_v1(
            pack_id="dpm_pm_memo.pack",
            workflow_surface="dpm-proof-pack-ai-evidence",
            correlation_id="corr-proof-pack-memo-1",
        ),
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0040"
    assert response.data.workflow_pack_run.workflow_authority_owner == "lotus-manage"


def test_dpm_proof_pack_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    expected_paths = [
        ("/api/v1/dpm/command-center/proof-packs", "post"),
        ("/api/v1/dpm/command-center/proof-packs/{proof_pack_id}", "get"),
        ("/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/summary.md", "get"),
        ("/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/report-input", "get"),
        ("/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-evidence-input", "get"),
        ("/api/v1/dpm/command-center/proof-packs/{proof_pack_id}/ai-pm-memo", "post"),
    ]

    for path, method in expected_paths:
        assert path in spec["paths"]
        operation = spec["paths"][path][method]
        assert operation["tags"] == ["DPM Command Center"]
        assert operation["summary"]
        assert "What:" in operation["description"]
        assert "When:" in operation["description"]
        assert "How:" in operation["description"]


def test_dpm_proof_pack_openapi_models_are_described() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]

    for schema_name in [
        "DpmProofPackGenerateRequest",
        "DpmProofPackGatewayResponse",
        "DpmProofPackMarkdownResponse",
        "DpmProofPackMemoGatewayResponse",
        "DpmProofPackMemoRequest",
        "DpmProofPackSupportability",
        "DpmProofPackErrorDetail",
    ]:
        schema = schemas[schema_name]
        for property_schema in schema["properties"].values():
            assert property_schema.get("description")

    assert schemas["DpmProofPackGenerateRequest"]["properties"]["body"]["examples"]
    assert schemas["DpmProofPackGatewayResponse"]["properties"]["data"]["description"]
    assert schemas["DpmProofPackSupportability"]["properties"]["state"]["examples"]
