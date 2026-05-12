from fastapi.testclient import TestClient

from app.contracts.dpm_waves import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmWaveGatewayResponse,
    DpmWaveMemoGatewayResponse,
)
from app.main import app


def test_dpm_wave_gateway_response_contract_shape() -> None:
    response = DpmWaveGatewayResponse(
        correlation_id="corr-wave-1",
        upstream_status=200,
        supportability={
            "state": "ready",
            "reason_codes": ["wave_supportability_ready"],
            "wave_id": "dwv_001",
            "wave_state": "HANDOFF_READY",
            "item_count": 2,
        },
        data={
            "wave": {
                "wave_id": "dwv_001",
                "state": "HANDOFF_READY",
                "aggregate_metrics": {"item_count": 2},
            },
            "durable": True,
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.supportability.wave_id == "dwv_001"
    assert response.data["wave"]["state"] == "HANDOFF_READY"


def test_dpm_wave_memo_gateway_response_contract_shape() -> None:
    response = DpmWaveMemoGatewayResponse(
        correlation_id="corr-wave-ai-memo",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={"state": "ready", "reason_codes": ["wave_report_input_ready"]},
        wave_report_input={
            "wave_id": "dwv_001",
            "report_input_ref": "report-input:dwv_001",
        },
        memo_request={
            "requested_outputs": ["wave_pm_memo", "approval_checklist"],
            "audience": ["portfolio_manager", "investment_control"],
        },
        data={"run_id": "wf_run_wave_memo_001", "status": "REVIEW_REQUIRED"},
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.wave_report_input["wave_id"] == "dwv_001"


def test_dpm_operations_handoff_summary_gateway_response_contract_shape() -> None:
    response = DpmOperationsHandoffSummaryGatewayResponse(
        correlation_id="corr-wave-handoff-summary",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={"state": "ready", "reason_codes": ["wave_report_input_ready"]},
        wave_report_input={
            "wave_id": "dwv_001",
            "handoff_refs": [{"ref_id": "handoff_001"}],
            "external_execution_claimed": False,
        },
        handoff_summary_request={
            "requested_outputs": ["operations_summary", "blocking_conditions"],
            "audience": ["operations", "portfolio_manager"],
        },
        data={"run_id": "wf_run_handoff_001", "status": "REVIEW_REQUIRED"},
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.wave_report_input["external_execution_claimed"] is False


def test_dpm_wave_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    expected_paths = [
        ("/api/v1/dpm/command-center/waves/preview", "post"),
        ("/api/v1/dpm/command-center/waves", "post"),
        ("/api/v1/dpm/command-center/waves", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/items", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/source-check", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/simulate", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/items/{wave_item_id}/select", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/approve", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/stage", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/handoff", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/cancel", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/proof-pack", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/supportability", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/report-input", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/ai-pm-memo", "post"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/operations-handoff-summary", "post"),
    ]

    for path, method in expected_paths:
        assert path in spec["paths"]
        operation = spec["paths"][path][method]
        assert operation["tags"] == ["DPM Command Center"]
        assert operation["summary"]
        assert "What:" in operation["description"]
        assert "When:" in operation["description"]
        assert "How:" in operation["description"]


def test_dpm_wave_openapi_models_are_described() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]

    for schema_name in [
        "DpmWaveCreateRequest",
        "DpmWaveForwardRequest",
        "DpmWaveGatewayResponse",
        "DpmOperationsHandoffSummaryGatewayResponse",
        "DpmOperationsHandoffSummaryRequest",
        "DpmWaveMemoGatewayResponse",
        "DpmWaveMemoRequest",
        "DpmWaveSupportability",
        "DpmWaveErrorDetail",
    ]:
        schema = schemas[schema_name]
        for property_schema in schema["properties"].values():
            assert property_schema.get("description")

    assert schemas["DpmWaveSupportability"]["properties"]["state"]["examples"]
    assert schemas["DpmWaveGatewayResponse"]["properties"]["data"]["description"]
