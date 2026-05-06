from fastapi.testclient import TestClient

from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
)
from app.main import app


def test_dpm_outcome_review_gateway_response_contract_shape() -> None:
    response = DpmOutcomeReviewGatewayResponse(
        correlation_id="corr-1",
        upstream_status=200,
        supportability={
            "state": "SUPPORTED",
            "reason_codes": ["READY_FOR_REPORT_INPUT"],
            "blocked_actions": [],
        },
        data={
            "outcome_review_id": "or_1",
            "state": "READY",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "expected_snapshot_hash": "sha256:expected",
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042"
    assert response.data["outcome_review_id"] == "or_1"


def test_dpm_command_center_gateway_response_contract_shape() -> None:
    response = DpmCommandCenterGatewayResponse(
        correlation_id="corr-rfc38-1",
        upstream_status=200,
        supportability={
            "state": "PARTIAL",
            "data_completeness_state": "PARTIAL",
            "partial_readiness_reasons": ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"],
            "source_run_id": "dmr_1",
        },
        data={
            "health_distribution": {"READY": 3, "PENDING_REVIEW": 1},
            "active_exception_count": 1,
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0038"
    assert response.supportability.partial_readiness_reasons == ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"]
    assert response.data["health_distribution"] == {"READY": 3, "PENDING_REVIEW": 1}


def test_dpm_outcome_review_narrative_gateway_response_contract_shape() -> None:
    response = DpmOutcomeReviewNarrativeGatewayResponse(
        correlation_id="corr-1",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={"state": "SUPPORTED"},
        ai_evidence_input={
            "outcome_review_id": "or_1",
            "content_hash": "sha256:ai-evidence",
        },
        narrative_request={"requested_outputs": ["pm_summary"], "audience": ["pm"]},
        data={
            "execution": {"status": "COMPLETED"},
            "workflow_pack_run": {"workflow_authority_owner": "lotus-manage"},
        },
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042"
    assert response.data["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def test_dpm_command_center_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    expected_paths = [
        ("/api/v1/dpm/command-center", "get"),
        ("/api/v1/dpm/command-center/monitoring/run-once", "post"),
        ("/api/v1/dpm/command-center/monitoring/runs", "get"),
        ("/api/v1/dpm/command-center/monitoring/runs/{monitoring_run_id}", "get"),
        ("/api/v1/dpm/command-center/exceptions", "get"),
        ("/api/v1/dpm/command-center/exceptions/{exception_id}/resolve", "post"),
        ("/api/v1/dpm/command-center/mandates/by-portfolio/{portfolio_id}", "get"),
        ("/api/v1/dpm/command-center/mandates/{mandate_id}", "get"),
        ("/api/v1/dpm/command-center/mandates/{mandate_id}/health", "get"),
        ("/api/v1/dpm/command-center/mandates/{mandate_id}/diff", "get"),
        ("/api/v1/dpm/command-center/outcome-reviews/preview", "post"),
        ("/api/v1/dpm/command-center/outcome-reviews", "get"),
        ("/api/v1/dpm/command-center/outcome-reviews", "post"),
        ("/api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}", "get"),
        ("/api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/refresh-sources", "post"),
        ("/api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/supportability", "get"),
        ("/api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/report-input", "get"),
        ("/api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/ai-evidence-input", "get"),
        ("/api/v1/dpm/command-center/outcome-reviews/{outcome_review_id}/ai-narrative", "post"),
        ("/api/v1/dpm/command-center/runs/{rebalance_run_id}/outcome-review", "get"),
        ("/api/v1/dpm/command-center/waves/{wave_id}/outcome-reviews", "get"),
    ]

    for path, method in expected_paths:
        assert path in spec["paths"]
        operation = spec["paths"][path][method]
        assert operation["tags"] == ["DPM Command Center"]
        assert operation["summary"]
        assert "What:" in operation["description"]
        assert "When:" in operation["description"]
        assert "How:" in operation["description"]


def test_dpm_command_center_openapi_models_are_described() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]
    command_center_response_schema = schemas["DpmCommandCenterGatewayResponse"]
    command_center_supportability_schema = schemas["DpmCommandCenterSupportability"]
    response_schema = schemas["DpmOutcomeReviewGatewayResponse"]
    narrative_response_schema = schemas["DpmOutcomeReviewNarrativeGatewayResponse"]
    supportability_schema = schemas["DpmOutcomeReviewSupportability"]

    for property_schema in command_center_response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in command_center_supportability_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in supportability_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in narrative_response_schema["properties"].values():
        assert property_schema.get("description")

    assert command_center_response_schema["properties"]["data"]["description"]
    assert command_center_supportability_schema["properties"]["state"]["examples"]
    assert response_schema["properties"]["data"]["description"]
    assert narrative_response_schema["properties"]["data"]["description"]
    assert supportability_schema["properties"]["state"]["examples"]
