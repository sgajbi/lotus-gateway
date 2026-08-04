from fastapi.testclient import TestClient

from app.contracts.dpm_waves import (
    DpmCampaignWorkflowGatewayResponse,
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmWaveGatewayResponse,
    DpmWaveMemoGatewayResponse,
)
from app.main import app
from tests.support.lotus_ai_workflow_pack import lotus_ai_workflow_pack_execution_v1


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
        data=lotus_ai_workflow_pack_execution_v1(
            pack_id="dpm_wave_pm_memo.pack",
            workflow_surface="dpm-wave-ai-evidence",
            correlation_id="corr-wave-ai-memo",
        ),
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.wave_report_input["wave_id"] == "dwv_001"
    assert response.data.workflow_pack_run.review_state == "AWAITING_REVIEW"


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
        data=lotus_ai_workflow_pack_execution_v1(
            pack_id="dpm_operations_handoff_summary.pack",
            workflow_surface="dpm-operations-handoff-ai-evidence",
            correlation_id="corr-wave-handoff-summary",
        ),
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.wave_report_input["external_execution_claimed"] is False
    assert response.data.workflow_pack_run.review_required is True


def test_dpm_campaign_workflow_gateway_response_contract_shape() -> None:
    response = DpmCampaignWorkflowGatewayResponse(
        correlation_id="corr-campaign-workflow",
        upstream_status=200,
        data={
            "product_name": "BulkReviewCampaignOperatingQueue",
            "items": [{"task_ref": "task-review-001", "content_hash": "sha256:task"}],
            "count": 1,
            "limit": 50,
            "offset": 0,
            "operating_boundaries": [
                "NO_ORDER_GENERATION",
                "NO_OMS_EXECUTION_CLAIM",
                "NO_EXTERNAL_WORKFLOW_ORCHESTRATION",
            ],
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.data["count"] == 1
    assert "NO_OMS_EXECUTION_CLAIM" in response.data["operating_boundaries"]


def test_dpm_wave_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    expected_paths = [
        ("/api/v1/dpm/command-center/waves/preview", "post"),
        ("/api/v1/dpm/command-center/waves", "post"),
        ("/api/v1/dpm/command-center/waves", "get"),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}",
            "put",
        ),
        ("/api/v1/dpm/command-center/waves/campaign-definitions", "get"),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/lifecycle-events",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/preview-readiness",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-history",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch-package",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/launch",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/retire",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/supersede",
            "post",
        ),
        ("/api/v1/dpm/command-center/waves/campaign-discovery", "get"),
        ("/api/v1/dpm/command-center/waves/campaign-operating-queue", "get"),
        ("/api/v1/dpm/command-center/waves/campaign-approval-inbox", "get"),
        ("/api/v1/dpm/command-center/waves/campaign-workflow-board", "get"),
        ("/api/v1/dpm/command-center/waves/campaign-assignment-plan", "get"),
        ("/api/v1/dpm/command-center/waves/campaign-workflow-automation", "get"),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/approval-decisions",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-actions",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks/{task_ref}/transitions",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/maker-checker-controls",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/waves/campaign-definitions/{campaign_id}/versions/{campaign_version}/maker-checker-controls",
            "post",
        ),
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
        "DpmCampaignDefinitionForwardRequest",
        "DpmCampaignDefinitionLaunchRequest",
        "DpmCampaignDefinitionLifecycleCommandRequest",
        "DpmCampaignDefinitionGatewayResponse",
        "DpmCampaignWorkflowForwardRequest",
        "DpmCampaignWorkflowGatewayResponse",
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
    wave_forward_body = schemas["DpmWaveForwardRequest"]["properties"]["body"]
    assert "DpmPortfolioUniverseCandidate:v1" in wave_forward_body["description"]
    assert "CORE_DPM_PORTFOLIO_UNIVERSE" in str(wave_forward_body["examples"])
    assert "caller-supplied candidate portfolios" in wave_forward_body["description"]
