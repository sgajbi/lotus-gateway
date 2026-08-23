from fastapi.testclient import TestClient

from app.main import app


def test_all_dpm_ai_handoffs_publish_one_typed_execution_contract() -> None:
    schemas = TestClient(app).get("/openapi.json").json()["components"]["schemas"]
    execution_ref = "#/components/schemas/DpmAiWorkflowExecution"

    for response_schema in (
        "DpmProofPackMemoGatewayResponse",
        "DpmWaveMemoGatewayResponse",
        "DpmOperationsHandoffSummaryGatewayResponse",
        "DpmExceptionSummaryGatewayResponse",
        "DpmOutcomeReviewNarrativeGatewayResponse",
        "DpmPmOperatingQualitySummaryGatewayResponse",
    ):
        data_schema = schemas[response_schema]["properties"]["data"]
        assert data_schema["$ref"] == execution_ref
        assert data_schema["description"]


def test_dpm_ai_execution_openapi_preserves_product_evidence_and_excludes_raw_fields() -> None:
    schemas = TestClient(app).get("/openapi.json").json()["components"]["schemas"]

    execution_properties = schemas["DpmAiWorkflowExecution"]["properties"]
    run_properties = schemas["DpmAiWorkflowPackRun"]["properties"]
    result_properties = schemas["DpmAiTaskResult"]["properties"]
    audit_properties = schemas["DpmAiTaskAudit"]["properties"]
    evidence_properties = schemas["DpmAiExecutionEvidenceDescriptor"]["properties"]
    artifact_properties = schemas["DpmAiArtifactReference"]["properties"]

    assert audit_properties["provider_mode"]["enum"] == [
        "disabled",
        "stub",
        "openai",
        "local_openai_compatible",
    ]
    assert run_properties["provider_mode"]["enum"] == [
        "disabled",
        "stub",
        "openai",
        "local_openai_compatible",
    ]

    for field in ("eligibility", "execution", "workflow_pack_run", "summary"):
        assert field in execution_properties
    for field in (
        "runtime_state",
        "review_state",
        "supportability_status",
        "review_required",
        "review_summary",
        "evidence_descriptors",
        "artifact_refs",
        "supersedes_run_id",
        "superseded_by_run_id",
        "replacement_run_id",
        "recovery_lineage",
        "created_at",
        "completed_at",
        "last_updated_at",
    ):
        assert field in run_properties

    assert set(result_properties) == {"structured_output"}
    assert "prompt_version" not in audit_properties
    assert "prompt_selection" not in audit_properties
    assert "attributes" not in evidence_properties
    assert "output_preview" not in run_properties
    assert "storage_reference" not in artifact_properties
    assert "storage_backend" not in artifact_properties
    assert "created_by" not in artifact_properties

    for schema_name in (
        "DpmAiWorkflowExecution",
        "DpmAiTaskExecution",
        "DpmAiTaskAudit",
        "DpmAiWorkflowPackRun",
        "DpmAiWorkflowReviewSummary",
        "DpmAiExecutionEvidenceDescriptor",
        "DpmAiArtifactReference",
        "DpmAiRecoveryLineage",
    ):
        for property_schema in schemas[schema_name]["properties"].values():
            assert property_schema.get("description")
