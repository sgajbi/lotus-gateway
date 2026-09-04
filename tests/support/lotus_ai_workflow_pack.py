"""Versioned lotus-ai WorkflowPackExecutionResponse fixture builders."""

from typing import Any

LOTUS_AI_WORKFLOW_PACK_EXECUTION_FIXTURE_VERSION = "WorkflowPackExecutionResponse.v1"
UNSAFE_UPSTREAM_MARKER = "unsafe-upstream-generated-content"


def lotus_ai_workflow_pack_execution_v1(
    *,
    pack_id: str,
    workflow_surface: str,
    correlation_id: str,
    structured_output: dict[str, object] | None = None,
    runtime_state: str = "COMPLETED",
    review_state: str = "AWAITING_REVIEW",
    supportability_status: str = "ACTION_REQUIRED",
    review_required: bool = True,
    stubbed: bool = True,
    supersedes_run_id: str | None = None,
    superseded_by_run_id: str | None = None,
    replacement_run_id: str | None = None,
    recovery_lineage: dict[str, object] | None = None,
    output_validation: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Build the bounded peer-service success shape published by lotus-ai."""

    pack_family = pack_id.removesuffix(".pack")
    run_id = f"packrun_{pack_family}_001"
    request_id = f"air_{pack_family}_001"
    provider_mode = "disabled" if stubbed else "openai"
    provider_id = "text.stub" if stubbed else "text.openai"
    adapter_kind = "STUB" if stubbed else "OPENAI"
    output = structured_output or {
        "workflow_pack_family": pack_family,
        "state": "REVIEW_REQUIRED",
        "scope": "support_only",
    }
    allowed_review_actions = (
        ["ACCEPT", "REJECT", "REVISE", "SUPERSEDE", "ABANDON"]
        if review_required and review_state == "AWAITING_REVIEW"
        else []
    )
    return {
        "service": "lotus-ai",
        "version": "0.1.0",
        "eligibility": {
            "service": "lotus-ai",
            "version": "0.1.0",
            "pack_id": pack_id,
            "requested_version": "v1",
            "eligibility_result": "ALLOWED",
            "allowed": True,
            "evaluated_registration_ref": f"{pack_id}@v1",
            "caller_app": "lotus-gateway",
            "environment": "DEVELOPMENT",
            "caller_identity_class": "INTERNAL_SERVICE",
            "tenant_scope_applied": False,
            "workflow_surface_applied": True,
            "denial_reasons": [],
            "status_summary": ["Workflow execution is eligible."],
        },
        "execution": {
            "status": "COMPLETED" if runtime_state != "FAILED" else "FAILED",
            "task_id": "explain.v1",
            "category": "explain",
            "output_label": "EXPLANATION_ONLY",
            "result": {
                "message": UNSAFE_UPSTREAM_MARKER,
                "structured_output": output,
            },
            "output_validation": (
                output_validation
                if output_validation is not None
                else {
                    "validation_state": "VALIDATED",
                    "authority": "non_authoritative_ai_output",
                    "ruleset_version": "output-validation.v4",
                    "failed_rule_ids": [],
                    "findings": [],
                }
            ),
            "audit": {
                "request_id": request_id,
                "workflow_pack_run_id": run_id,
                "task_id": "explain.v1",
                "output_label": "EXPLANATION_ONLY",
                "prompt_version": "foundation.explain.v1",
                "prompt_selection": {"unsafe_prompt_detail": UNSAFE_UPSTREAM_MARKER},
                "provider_mode": provider_mode,
                "provider_id": provider_id,
                "adapter_kind": adapter_kind,
                "model_id": None if stubbed else "gpt-5.4",
                "model_version": None if stubbed else "2026-06-01",
                "safety": {
                    "safety_mode": "documented_only",
                    "output_label": "EXPLANATION_ONLY",
                    "redaction_posture": "MINIMIZATION_REQUIRED",
                    "disposition": "DOCUMENTED_ONLY",
                    "runtime_redaction_active": False,
                    "enforced_controls": ["response_labeling", "correlation_and_audit"],
                    "control_results": [{"control_id": "raw", "summary": UNSAFE_UPSTREAM_MARKER}],
                    "decision_summary": UNSAFE_UPSTREAM_MARKER,
                },
                "authorization": {
                    "caller_app": "lotus-gateway",
                    "authenticated_caller_app": "lotus-gateway",
                    "caller_identity_source": "trusted_http_header",
                    "caller_identity_bound": True,
                    "capability_type": "task_execution",
                    "outcome": "ALLOWED",
                    "allowed": True,
                    "tenant_policy_mode": "OPTIONAL",
                    "task_id": "explain.v1",
                    "requested_source_ids": [],
                    "effective_source_ids": [],
                    "summary": UNSAFE_UPSTREAM_MARKER,
                },
                "generated_at": "2026-08-04T18:12:19Z",
                "stubbed": stubbed,
            },
            "evidence": {
                "descriptors": [
                    {
                        "evidence_type": "task_contract",
                        "summary": "The bounded task contract supported this execution.",
                        "attributes": {"raw_attribute": UNSAFE_UPSTREAM_MARKER},
                    }
                ]
            },
        },
        "workflow_pack_run": {
            "run_id": run_id,
            "pack_id": pack_id,
            "pack_family": pack_family,
            "pack_version": "v1",
            "registration_ref": f"{pack_id}@v1",
            "task_id": "explain.v1",
            "request_id": request_id,
            "caller_app": "lotus-gateway",
            "correlation_id": correlation_id,
            "tenant_id": "tenant-sg-001",
            "workflow_surface": workflow_surface,
            "workflow_authority_owner": "lotus-manage",
            "runtime_state": runtime_state,
            "review_state": review_state,
            "supportability_status": supportability_status,
            "allowed_review_actions": allowed_review_actions,
            "review_summary": {
                "latest_review_event_at": None,
                "latest_review_actor": None,
                "review_transition_count": 0,
                "has_review_history": False,
            },
            "review_required": review_required,
            "provider_mode": provider_mode,
            "stubbed": stubbed,
            "output_preview": UNSAFE_UPSTREAM_MARKER,
            "structured_output_keys": sorted(output),
            "evidence_descriptors": [
                {
                    "evidence_type": "task_contract",
                    "summary": "The bounded task contract supported this execution.",
                    "attributes": {"raw_attribute": UNSAFE_UPSTREAM_MARKER},
                }
            ],
            "artifact_refs": [
                {
                    "artifact_id": f"artifact_{pack_family}_001",
                    "domain": "workflow_pack",
                    "artifact_type": "run_output_summary",
                    "source_object_kind": "workflow_pack_run",
                    "source_object_id": run_id,
                    "lifecycle_status": "runtime_generated",
                    "retention_posture": "retained_for_review",
                    "media_type": "application/json",
                    "byte_size": 512,
                    "checksum_sha256": "a" * 64,
                    "storage_backend": "memory",
                    "storage_reference": f"memory://{UNSAFE_UPSTREAM_MARKER}",
                    "lineage_parent_artifact_id": None,
                    "superseded_by_artifact_id": None,
                    "created_at": "2026-08-04T18:12:19Z",
                    "created_by": UNSAFE_UPSTREAM_MARKER,
                }
            ],
            "supersedes_run_id": supersedes_run_id,
            "superseded_by_run_id": superseded_by_run_id,
            "replacement_run_id": replacement_run_id,
            "recovery_lineage": recovery_lineage,
            "created_at": "2026-08-04T18:12:19Z",
            "completed_at": "2026-08-04T18:12:19Z",
            "last_updated_at": "2026-08-04T18:12:19Z",
        },
        "summary": ["The governed workflow pack completed and requires review."],
    }
