from fastapi.testclient import TestClient

from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmExceptionSummaryGatewayResponse,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmPmOperatingQualityGatewayResponse,
    DpmPmOperatingQualitySummaryGatewayResponse,
    DpmPortfolioMemoryGatewayResponse,
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
            "client_communication_boundary": {
                "boundary_id": "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY",
                "supportability_state": "BLOCKED",
                "client_communication_projected": False,
                "client_approval_projected": False,
                "required_source_product": "ClientCommunicationRecord:v1",
            },
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042"
    assert response.data["outcome_review_id"] == "or_1"
    assert response.data["client_communication_boundary"]["boundary_id"] == (
        "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY"
    )
    assert response.data["client_communication_boundary"]["client_communication_projected"] is False
    assert response.data["client_communication_boundary"]["client_approval_projected"] is False
    assert response.data["client_communication_boundary"]["required_source_product"] == (
        "ClientCommunicationRecord:v1"
    )


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


def test_dpm_portfolio_memory_gateway_response_contract_shape() -> None:
    response = DpmPortfolioMemoryGatewayResponse(
        correlation_id="corr-rfc40-memory-1",
        upstream_status=200,
        supportability={
            "state": "READY",
            "event_count": 3,
            "event_type_counts": {
                "PROOF_PACK_CREATED": 1,
                "OUTCOME_REVIEW_CREATED": 1,
                "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION": 1,
            },
            "source_systems": ["lotus-manage", "lotus-core"],
            "reason_codes": ["SOURCE_READY"],
            "content_hash": "sha256:portfolio-memory",
        },
        data={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "event_count": 2,
            "supportability_state": "READY",
            "events": [{"event_type": "PROOF_PACK_CREATED"}],
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0040/RFC-0041/RFC-0042"
    assert response.supportability.event_type_counts == {
        "PROOF_PACK_CREATED": 1,
        "OUTCOME_REVIEW_CREATED": 1,
        "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION": 1,
    }
    assert response.data["portfolio_id"] == "PB_SG_GLOBAL_BAL_001"


def test_dpm_pm_operating_quality_gateway_response_contract_shape() -> None:
    response = DpmPmOperatingQualityGatewayResponse(
        correlation_id="corr-pmq-1",
        upstream_status=200,
        supportability={
            "state": "READY",
            "reason_codes": ["PM_QUALITY_READY"],
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "score_run_id": "pmq_run_001",
        },
        data={
            "score_run": {
                "product_name": "PmOperatingQualityScoreRun",
                "product_version": "v1",
                "score_run_id": "pmq_run_001",
                "state": "READY",
                "forbidden_uses": [
                    "compensation_decision",
                    "hr_decision",
                    "conduct_enforcement",
                    "autonomous_pm_ranking",
                ],
            }
        },
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042/PM_OPERATING_QUALITY"
    assert response.supportability.score_run_id == "pmq_run_001"
    assert response.data["score_run"]["forbidden_uses"] == [
        "compensation_decision",
        "hr_decision",
        "conduct_enforcement",
        "autonomous_pm_ranking",
    ]

    fairness_response = DpmPmOperatingQualityGatewayResponse(
        correlation_id="corr-pmq-fairness-1",
        upstream_status=200,
        supportability={
            "state": "PENDING_REVIEW",
            "reason_codes": ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"],
            "blocked_actions": ["CREATE_SCORE_RUN"],
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "fairness_analysis_id": "pmq_fair_001",
        },
        data={
            "fairness_analysis": {
                "product_name": "PmOperatingQualityFairnessAnalysis",
                "product_version": "v1",
                "fairness_analysis_id": "pmq_fair_001",
                "state": "PENDING_REVIEW",
                "segment_results": [
                    {
                        "segment_type": "MANDATE_TYPE",
                        "segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED",
                        "state": "REVIEW_REQUIRED",
                    }
                ],
                "forbidden_uses": [
                    "protected_class_inference",
                    "autonomous_pm_ranking",
                    "hr_decision",
                    "compensation_decision",
                    "conduct_enforcement",
                ],
            }
        },
    )
    assert fairness_response.supportability.fairness_analysis_id == "pmq_fair_001"
    assert fairness_response.data["fairness_analysis"]["segment_results"][0]["segment_type"] == (
        "MANDATE_TYPE"
    )

    review_action_response = DpmPmOperatingQualityGatewayResponse(
        correlation_id="corr-pmq-review-1",
        upstream_status=200,
        supportability={
            "state": "REVIEW_REQUIRED",
            "reason_codes": ["PM_QUALITY_REVIEW_ACTION_STATE_REVIEW_REQUIRED"],
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "review_action_id": "pmq_review_001",
        },
        data={
            "review_action": {
                "product_name": "PmOperatingQualityReviewAction",
                "product_version": "v1",
                "review_action_id": "pmq_review_001",
                "target_type": "SCORE_RUN",
                "target_id": "pmq_run_001",
                "target_content_hash": "sha256:pmq-run-001",
                "action_state": "REVIEW_REQUIRED",
                "review_reason": "Evidence remediation required before supervisory closure.",
                "forbidden_uses": [
                    "compensation_decision",
                    "hr_decision",
                    "conduct_enforcement",
                    "client_contact",
                    "trade_approval",
                    "order_routing",
                    "oms_execution",
                    "autonomous_pm_ranking",
                ],
                "operating_boundaries": [
                    "IMMUTABLE_REVIEW_ACTION_LEDGER",
                    "NO_SCORE_RECALCULATION",
                    "NO_FAIRNESS_RECOMPUTATION",
                    "NO_PM_RANKING",
                    "NO_HR_COMPENSATION_OR_CONDUCT_DECISION",
                    "NO_CLIENT_CONTACT",
                    "NO_TRADE_APPROVAL",
                    "NO_ORDER_OR_OMS_EXECUTION",
                ],
            }
        },
    )
    assert review_action_response.supportability.review_action_id == "pmq_review_001"
    assert review_action_response.data["review_action"]["target_content_hash"] == (
        "sha256:pmq-run-001"
    )

    summary_invocation_response = DpmPmOperatingQualityGatewayResponse(
        correlation_id="corr-pmq-summary-history-1",
        upstream_status=200,
        supportability={
            "state": "REQUESTED",
            "reason_codes": ["PM_QUALITY_SUMMARY_INVOCATION_REQUESTED"],
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "score_run_id": "pmq_run_001",
            "review_action_id": "pmq_review_001",
            "summary_invocation_id": "pmq_summary_001",
        },
        data={
            "summary_invocation": {
                "product_name": "PmOperatingQualitySummaryInvocation",
                "product_version": "v1",
                "summary_invocation_id": "pmq_summary_001",
                "score_run_id": "pmq_run_001",
                "review_action_id": "pmq_review_001",
                "invocation_state": "REQUESTED",
                "workflow_pack_name": "pm_quality_summary.pack",
                "workflow_run_id": "packrun_pmq_001",
                "summary_artifact_ref": "artifact://pmq-summary-001",
                "summary_content_hash": "sha256:pmq-summary-artifact-001",
                "text_boundary": {
                    "generated_summary_text_stored": False,
                    "prompt_body_stored": False,
                    "model_response_stored": False,
                },
                "operating_boundaries": [
                    "NO_GENERATED_SUMMARY_TEXT_RETENTION",
                    "NO_PROMPT_OR_MODEL_RESPONSE_EXPOSURE",
                    "NO_PM_RANKING",
                    "NO_CLIENT_CONTACT",
                    "NO_TRADE_ORDER_OR_OMS_EXECUTION",
                ],
            }
        },
    )
    assert summary_invocation_response.supportability.summary_invocation_id == ("pmq_summary_001")
    assert (
        summary_invocation_response.data["summary_invocation"]["text_boundary"][
            "model_response_stored"
        ]
        is False
    )


def test_dpm_outcome_review_narrative_gateway_response_contract_shape() -> None:
    response = DpmOutcomeReviewNarrativeGatewayResponse(
        correlation_id="corr-1",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={"state": "SUPPORTED"},
        ai_evidence_input={
            "outcome_review_id": "or_1",
            "content_hash": "sha256:ai-evidence",
            "client_communication_boundary": {
                "boundary_id": "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY",
                "supportability_state": "BLOCKED",
                "client_communication_projected": False,
                "client_approval_projected": False,
                "required_source_product": "ClientCommunicationRecord:v1",
            },
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
    assert response.ai_evidence_input["client_communication_boundary"]["boundary_id"] == (
        "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY"
    )
    assert response.data["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def test_dpm_exception_summary_gateway_response_contract_shape() -> None:
    response = DpmExceptionSummaryGatewayResponse(
        correlation_id="corr-exception-summary-1",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={"state": "READY", "data_completeness_state": "READY"},
        exception_summary_input={
            "contract_version": "1.0",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
            "exception_count": 1,
            "exceptions": [{"exception_id": "me_source_1", "state": "ACTIVE"}],
            "redaction_policy": "NO_RAW_PAYLOADS",
            "content_hash": "sha256:exception-summary",
        },
        exception_summary_request={
            "requested_outputs": ["exception_summary", "recommended_triage"],
            "audience": ["portfolio_manager", "operations"],
        },
        data={
            "execution": {"status": "COMPLETED"},
            "workflow_pack_run": {"workflow_authority_owner": "lotus-manage"},
        },
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0038"
    assert response.exception_summary_input["redaction_policy"] == "NO_RAW_PAYLOADS"
    assert response.data["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def test_dpm_pm_operating_quality_summary_gateway_response_contract_shape() -> None:
    response = DpmPmOperatingQualitySummaryGatewayResponse(
        correlation_id="corr-pmq-summary-1",
        manage_upstream_status=200,
        ai_upstream_status=200,
        supportability={
            "state": "READY",
            "reason_codes": ["PM_QUALITY_READY"],
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "score_run_id": "pmq_run_001",
        },
        score_run={
            "product_name": "PmOperatingQualityScoreRun",
            "product_version": "1.0",
            "score_run_id": "pmq_run_001",
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "state": "READY",
            "source_refs": [
                {
                    "source_system": "lotus-manage",
                    "source_type": "PmOperatingQualityScoreRun",
                    "source_id": "pmq_run_001",
                }
            ],
            "content_hash": "sha256:pmq-run-001",
        },
        summary_request={
            "requested_outputs": ["score_run_summary", "support_references"],
            "audience": ["portfolio_manager", "investment_control"],
        },
        data={
            "execution": {"status": "COMPLETED"},
            "workflow_pack_run": {"workflow_authority_owner": "lotus-manage"},
        },
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042/PM_OPERATING_QUALITY"
    assert response.score_run["score_run_id"] == "pmq_run_001"
    assert response.summary_request["requested_outputs"] == [
        "score_run_summary",
        "support_references",
    ]
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
        ("/api/v1/dpm/command-center/exceptions/{exception_id}/ai-summary", "post"),
        ("/api/v1/dpm/command-center/mandates/by-portfolio/{portfolio_id}", "get"),
        ("/api/v1/dpm/command-center/mandates/{mandate_id}", "get"),
        ("/api/v1/dpm/command-center/mandates/{mandate_id}/health", "get"),
        ("/api/v1/dpm/command-center/mandates/{mandate_id}/diff", "get"),
        ("/api/v1/dpm/command-center/portfolios/{portfolio_id}/memory", "get"),
        ("/api/v1/dpm/command-center/pm-operating-quality/score-runs/preview", "post"),
        ("/api/v1/dpm/command-center/pm-operating-quality/score-runs", "get"),
        ("/api/v1/dpm/command-center/pm-operating-quality/score-runs", "post"),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses/preview",
            "post",
        ),
        ("/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses", "get"),
        ("/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses", "post"),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/"
            "fairness-analyses/{fairness_analysis_id}",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/review-actions/preview",
            "post",
        ),
        ("/api/v1/dpm/command-center/pm-operating-quality/review-actions", "get"),
        ("/api/v1/dpm/command-center/pm-operating-quality/review-actions", "post"),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/review-actions/{review_action_id}",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations/preview",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/"
            "summary-invocations/{summary_invocation_id}",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/score-runs/{score_run_id}",
            "get",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/score-runs/{score_run_id}/ai-summary",
            "post",
        ),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/policies/"
            "{policy_id}/versions/{policy_version}",
            "put",
        ),
        ("/api/v1/dpm/command-center/pm-operating-quality/policies", "get"),
        (
            "/api/v1/dpm/command-center/pm-operating-quality/policies/"
            "{policy_id}/versions/{policy_version}",
            "get",
        ),
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
        ("/api/v1/dpm/command-center/portfolio-memory/search", "get"),
    ]

    for path, method in expected_paths:
        assert path in spec["paths"]
        operation = spec["paths"][path][method]
        assert operation["tags"] == ["DPM Command Center"]
        assert operation["summary"]
        assert "What:" in operation["description"]
        assert "When:" in operation["description"]
        assert "How:" in operation["description"]
        assert operation["responses"]["409"]["description"]
        assert operation["responses"]["422"]["description"]
        assert operation["responses"]["503"]["description"]


def test_dpm_command_center_openapi_models_are_described() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    schemas = spec["components"]["schemas"]
    command_center_response_schema = schemas["DpmCommandCenterGatewayResponse"]
    command_center_supportability_schema = schemas["DpmCommandCenterSupportability"]
    portfolio_memory_response_schema = schemas["DpmPortfolioMemoryGatewayResponse"]
    portfolio_memory_supportability_schema = schemas["DpmPortfolioMemorySupportability"]
    pm_quality_response_schema = schemas["DpmPmOperatingQualityGatewayResponse"]
    pm_quality_supportability_schema = schemas["DpmPmOperatingQualitySupportability"]
    pm_quality_summary_request_schema = schemas["DpmPmOperatingQualitySummaryRequest"]
    pm_quality_summary_response_schema = schemas["DpmPmOperatingQualitySummaryGatewayResponse"]
    response_schema = schemas["DpmOutcomeReviewGatewayResponse"]
    narrative_response_schema = schemas["DpmOutcomeReviewNarrativeGatewayResponse"]
    exception_summary_request_schema = schemas["DpmExceptionSummaryRequest"]
    exception_summary_response_schema = schemas["DpmExceptionSummaryGatewayResponse"]
    supportability_schema = schemas["DpmOutcomeReviewSupportability"]

    for property_schema in command_center_response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in command_center_supportability_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in portfolio_memory_response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in portfolio_memory_supportability_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in pm_quality_response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in pm_quality_supportability_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in pm_quality_summary_request_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in pm_quality_summary_response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in supportability_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in narrative_response_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in exception_summary_request_schema["properties"].values():
        assert property_schema.get("description")

    for property_schema in exception_summary_response_schema["properties"].values():
        assert property_schema.get("description")

    assert command_center_response_schema["properties"]["data"]["description"]
    assert command_center_supportability_schema["properties"]["state"]["examples"]
    assert portfolio_memory_response_schema["properties"]["data"]["description"]
    assert portfolio_memory_supportability_schema["properties"]["state"]["examples"]
    assert pm_quality_response_schema["properties"]["data"]["description"]
    assert pm_quality_supportability_schema["properties"]["state"]["examples"]
    assert pm_quality_summary_request_schema["properties"]["requested_outputs"]["examples"]
    assert pm_quality_summary_response_schema["properties"]["data"]["description"]
    assert response_schema["properties"]["data"]["description"]
    assert "client_communication_boundary" in response_schema["properties"]["data"]["description"]
    assert narrative_response_schema["properties"]["data"]["description"]
    assert (
        "client_communication_boundary"
        in narrative_response_schema["properties"]["ai_evidence_input"]["description"]
    )
    assert exception_summary_request_schema["properties"]["requested_outputs"]["examples"]
    assert exception_summary_response_schema["properties"]["data"]["description"]
    assert supportability_schema["properties"]["state"]["examples"]
