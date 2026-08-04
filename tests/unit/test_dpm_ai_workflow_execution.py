from copy import deepcopy

import pytest
from fastapi import HTTPException, status

from app.services.dpm_ai_workflow_execution import (
    DPM_EXCEPTION_SUMMARY_EXECUTION,
    DPM_OPERATIONS_HANDOFF_EXECUTION,
    DPM_OUTCOME_REVIEW_NARRATIVE_EXECUTION,
    DPM_PM_OPERATING_QUALITY_EXECUTION,
    DPM_PROOF_PACK_PM_MEMO_EXECUTION,
    DPM_WAVE_PM_MEMO_EXECUTION,
    DpmAiWorkflowExecutionExpectation,
    validate_dpm_ai_workflow_execution,
)
from tests.support.lotus_ai_workflow_pack import (
    UNSAFE_UPSTREAM_MARKER,
    lotus_ai_workflow_pack_execution_v1,
)

_EXPECTATIONS = (
    DPM_PROOF_PACK_PM_MEMO_EXECUTION,
    DPM_WAVE_PM_MEMO_EXECUTION,
    DPM_OPERATIONS_HANDOFF_EXECUTION,
    DPM_EXCEPTION_SUMMARY_EXECUTION,
    DPM_OUTCOME_REVIEW_NARRATIVE_EXECUTION,
    DPM_PM_OPERATING_QUALITY_EXECUTION,
)


@pytest.mark.parametrize("expectation", _EXPECTATIONS)
def test_validate_dpm_ai_execution_preserves_each_governed_family(
    expectation: DpmAiWorkflowExecutionExpectation,
) -> None:
    correlation_id = f"corr-{expectation.pack_id}"
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=expectation.pack_id,
        workflow_surface=expectation.workflow_surface,
        correlation_id=correlation_id,
        structured_output={"state": "REVIEW_REQUIRED", "scope": "support_only"},
    )

    execution = validate_dpm_ai_workflow_execution(
        payload,
        upstream_status=200,
        correlation_id=correlation_id,
        expectation=expectation,
    )

    assert execution.workflow_pack_run.pack_id == expectation.pack_id
    assert execution.workflow_pack_run.runtime_state == "COMPLETED"
    assert execution.workflow_pack_run.review_state == "AWAITING_REVIEW"
    assert execution.workflow_pack_run.review_required is True
    assert execution.workflow_pack_run.stubbed is True
    assert execution.execution.result.structured_output["scope"] == "support_only"


def test_validate_dpm_ai_execution_strips_untrusted_non_product_fields() -> None:
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=DPM_PROOF_PACK_PM_MEMO_EXECUTION.pack_id,
        workflow_surface=DPM_PROOF_PACK_PM_MEMO_EXECUTION.workflow_surface,
        correlation_id="corr-safe-projection",
    )

    execution = validate_dpm_ai_workflow_execution(
        payload,
        upstream_status=200,
        correlation_id="corr-safe-projection",
        expectation=DPM_PROOF_PACK_PM_MEMO_EXECUTION,
    )
    serialized = execution.model_dump_json()

    assert UNSAFE_UPSTREAM_MARKER not in serialized
    assert "output_preview" not in serialized
    assert "prompt_selection" not in serialized
    assert "storage_reference" not in serialized
    assert "attributes" not in serialized
    assert execution.execution.result.structured_output["scope"] == "support_only"


def test_validate_dpm_ai_execution_preserves_live_provider_and_recovery_lineage() -> None:
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=DPM_OPERATIONS_HANDOFF_EXECUTION.pack_id,
        workflow_surface=DPM_OPERATIONS_HANDOFF_EXECUTION.workflow_surface,
        correlation_id="corr-live-replay",
        stubbed=False,
        recovery_lineage={
            "recovery_action_type": "REPLAY",
            "source_queue_item_id": "queue-item-001",
            "recovery_decision_event_id": "queue-event-001",
            "recovery_attempt_number": 2,
            "source_workflow_pack_run_id": "packrun-original-001",
            "requested_by": "operations-control",
            "evidence_ref": "replay-evidence-001",
        },
    )

    execution = validate_dpm_ai_workflow_execution(
        payload,
        upstream_status=200,
        correlation_id="corr-live-replay",
        expectation=DPM_OPERATIONS_HANDOFF_EXECUTION,
    )

    assert execution.execution.audit.stubbed is False
    assert execution.execution.audit.model_id == "gpt-5.4"
    assert execution.workflow_pack_run.recovery_lineage is not None
    assert execution.workflow_pack_run.recovery_lineage.recovery_action_type == "REPLAY"


def test_validate_dpm_ai_execution_preserves_superseded_replacement_posture() -> None:
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=DPM_OUTCOME_REVIEW_NARRATIVE_EXECUTION.pack_id,
        workflow_surface=DPM_OUTCOME_REVIEW_NARRATIVE_EXECUTION.workflow_surface,
        correlation_id="corr-superseded-run",
        runtime_state="SUPERSEDED",
        review_state="SUPERSEDED",
        supportability_status="HISTORICAL",
        superseded_by_run_id="packrun-replacement-001",
        replacement_run_id="packrun-replacement-001",
    )

    execution = validate_dpm_ai_workflow_execution(
        payload,
        upstream_status=200,
        correlation_id="corr-superseded-run",
        expectation=DPM_OUTCOME_REVIEW_NARRATIVE_EXECUTION,
    )

    assert execution.workflow_pack_run.runtime_state == "SUPERSEDED"
    assert execution.workflow_pack_run.review_state == "SUPERSEDED"
    assert execution.workflow_pack_run.supportability_status == "HISTORICAL"
    assert execution.workflow_pack_run.replacement_run_id == "packrun-replacement-001"


@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(lambda payload: payload.pop("workflow_pack_run"), id="missing-run"),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].pop("review_state"),
            id="missing-review-state",
        ),
        pytest.param(
            lambda payload: payload["execution"].update({"task_id": "wrong-task"}),
            id="execution-audit-task",
        ),
        pytest.param(
            lambda payload: payload["execution"].update({"output_label": "WRONG"}),
            id="execution-audit-label",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"]["safety"].update(
                {"output_label": "WRONG"}
            ),
            id="execution-safety-label",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"]["authorization"].update(
                {"task_id": "wrong-task"}
            ),
            id="execution-authorization-task",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"].update(
                {"workflow_pack_run_id": "wrong-run"}
            ),
            id="audit-run",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update({"task_id": "wrong-task"}),
            id="execution-run-task",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update({"request_id": "wrong-request"}),
            id="audit-run-request",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update({"stubbed": False}),
            id="audit-run-stub",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update(
                {"provider_mode": "wrong-provider"}
            ),
            id="audit-run-provider",
        ),
        pytest.param(
            lambda payload: payload["eligibility"].update({"pack_id": "wrong.pack"}),
            id="eligibility-run-pack",
        ),
        pytest.param(
            lambda payload: payload["eligibility"].update({"requested_version": "v2"}),
            id="eligibility-run-version",
        ),
        pytest.param(
            lambda payload: payload["eligibility"].update({"caller_app": "wrong-caller"}),
            id="eligibility-run-caller",
        ),
        pytest.param(
            lambda payload: payload["eligibility"].update(
                {"evaluated_registration_ref": "wrong.pack@v1"}
            ),
            id="eligibility-run-registration",
        ),
        pytest.param(
            lambda payload: payload["eligibility"].update({"version": "wrong-version"}),
            id="eligibility-service-version",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update(
                {"structured_output_keys": ["wrong_key"]}
            ),
            id="run-structured-output-keys",
        ),
        pytest.param(
            lambda payload: payload["eligibility"].update({"allowed": False}),
            id="eligibility-denied",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"]["authorization"].update(
                {"allowed": False}
            ),
            id="authorization-denied",
        ),
        pytest.param(
            lambda payload: (
                payload["eligibility"].update(
                    {
                        "pack_id": "wrong.pack",
                        "evaluated_registration_ref": "wrong.pack@v1",
                    }
                ),
                payload["workflow_pack_run"].update(
                    {"pack_id": "wrong.pack", "registration_ref": "wrong.pack@v1"}
                ),
            ),
            id="unexpected-pack",
        ),
        pytest.param(
            lambda payload: (
                payload["eligibility"].update(
                    {
                        "requested_version": "v2",
                        "evaluated_registration_ref": (
                            f"{DPM_EXCEPTION_SUMMARY_EXECUTION.pack_id}@v2"
                        ),
                    }
                ),
                payload["workflow_pack_run"].update(
                    {
                        "pack_version": "v2",
                        "registration_ref": f"{DPM_EXCEPTION_SUMMARY_EXECUTION.pack_id}@v2",
                    }
                ),
            ),
            id="unexpected-pack-version",
        ),
        pytest.param(
            lambda payload: (
                payload["eligibility"].update({"evaluated_registration_ref": "wrong.pack@v1"}),
                payload["workflow_pack_run"].update({"registration_ref": "wrong.pack@v1"}),
            ),
            id="unexpected-registration",
        ),
        pytest.param(
            lambda payload: (
                payload["eligibility"].update({"caller_app": "wrong-caller"}),
                payload["workflow_pack_run"].update({"caller_app": "wrong-caller"}),
            ),
            id="unexpected-caller",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update(
                {"correlation_id": "wrong-correlation"}
            ),
            id="unexpected-correlation",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update(
                {"workflow_surface": "wrong-surface"}
            ),
            id="unexpected-workflow-surface",
        ),
        pytest.param(
            lambda payload: payload["workflow_pack_run"].update(
                {"workflow_authority_owner": "wrong-authority"}
            ),
            id="unexpected-authority",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"]["authorization"].update(
                {"caller_app": "wrong-caller"}
            ),
            id="unexpected-authorized-caller",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"]["authorization"].update(
                {"authenticated_caller_app": "wrong-caller"}
            ),
            id="unexpected-authenticated-caller",
        ),
        pytest.param(
            lambda payload: payload["execution"]["audit"]["authorization"].update(
                {"caller_identity_bound": False}
            ),
            id="caller-identity-unbound",
        ),
    ),
)
def test_validate_dpm_ai_execution_fails_closed_without_leaking_source_payload(mutation) -> None:
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=DPM_EXCEPTION_SUMMARY_EXECUTION.pack_id,
        workflow_surface=DPM_EXCEPTION_SUMMARY_EXECUTION.workflow_surface,
        correlation_id="corr-invalid-contract",
    )
    malformed = deepcopy(payload)
    mutation(malformed)

    with pytest.raises(HTTPException) as raised:
        validate_dpm_ai_workflow_execution(
            malformed,
            upstream_status=200,
            correlation_id="corr-invalid-contract",
            expectation=DPM_EXCEPTION_SUMMARY_EXECUTION,
        )

    assert raised.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert raised.value.detail == {
        "source_service": "lotus-ai",
        "upstream_status": 200,
        "error_code": "AI_WORKFLOW_EXECUTION_CONTRACT_INVALID",
        "detail": "AI workflow output could not be safely verified.",
    }
    assert UNSAFE_UPSTREAM_MARKER not in str(raised.value.detail)
