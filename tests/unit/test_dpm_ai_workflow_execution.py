from copy import deepcopy
from typing import Any, Callable

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


def _replace_task_identity(payload: dict[str, Any]) -> None:
    payload["execution"]["task_id"] = "execute.client_action.v1"
    payload["execution"]["audit"]["task_id"] = "execute.client_action.v1"
    payload["execution"]["audit"]["authorization"]["task_id"] = "execute.client_action.v1"
    payload["workflow_pack_run"]["task_id"] = "execute.client_action.v1"


def _replace_output_label(payload: dict[str, Any]) -> None:
    payload["execution"]["output_label"] = "CLIENT_ACTION"
    payload["execution"]["audit"]["output_label"] = "CLIENT_ACTION"
    payload["execution"]["audit"]["safety"]["output_label"] = "CLIENT_ACTION"


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


@pytest.mark.parametrize("expectation", _EXPECTATIONS)
@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(_replace_task_identity, id="consistent-wrong-task"),
        pytest.param(_replace_output_label, id="consistent-wrong-output-label"),
    ),
)
def test_validate_dpm_ai_execution_binds_response_to_requested_task_contract(
    expectation: DpmAiWorkflowExecutionExpectation,
    mutation: Callable[[dict[str, Any]], None],
) -> None:
    correlation_id = f"corr-contract-{expectation.pack_id}"
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=expectation.pack_id,
        workflow_surface=expectation.workflow_surface,
        correlation_id=correlation_id,
    )
    mutation(payload)

    with pytest.raises(HTTPException) as raised:
        validate_dpm_ai_workflow_execution(
            payload,
            upstream_status=200,
            correlation_id=correlation_id,
            expectation=expectation,
        )

    assert raised.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert raised.value.detail["error_code"] == "AI_WORKFLOW_EXECUTION_CONTRACT_INVALID"
    assert "structured_output" not in str(raised.value.detail)


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


@pytest.mark.parametrize(
    ("provider_mode", "stubbed"),
    (
        ("disabled", False),
        ("stub", False),
        ("openai", True),
        ("local_openai_compatible", True),
        ("unknown", True),
    ),
)
def test_validate_dpm_ai_execution_rejects_invalid_provider_posture(
    provider_mode: object,
    stubbed: object,
) -> None:
    correlation_id = "corr-invalid-provider-posture"
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=DPM_PROOF_PACK_PM_MEMO_EXECUTION.pack_id,
        workflow_surface=DPM_PROOF_PACK_PM_MEMO_EXECUTION.workflow_surface,
        correlation_id=correlation_id,
    )
    payload["execution"]["audit"].update({"provider_mode": provider_mode, "stubbed": stubbed})
    payload["workflow_pack_run"].update({"provider_mode": provider_mode, "stubbed": stubbed})

    with pytest.raises(HTTPException) as raised:
        validate_dpm_ai_workflow_execution(
            payload,
            upstream_status=200,
            correlation_id=correlation_id,
            expectation=DPM_PROOF_PACK_PM_MEMO_EXECUTION,
        )

    assert raised.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert raised.value.detail["error_code"] == "AI_WORKFLOW_EXECUTION_CONTRACT_INVALID"
    assert str(provider_mode) not in str(raised.value.detail)


@pytest.mark.parametrize(
    "field_path",
    (
        pytest.param(("execution", "audit", "provider_mode"), id="missing-audit-mode"),
        pytest.param(("execution", "audit", "stubbed"), id="missing-audit-stub"),
        pytest.param(("workflow_pack_run", "provider_mode"), id="missing-run-mode"),
        pytest.param(("workflow_pack_run", "stubbed"), id="missing-run-stub"),
    ),
)
def test_validate_dpm_ai_execution_rejects_missing_provider_posture_fields(
    field_path: tuple[str, ...],
) -> None:
    correlation_id = "corr-missing-provider-posture"
    payload = lotus_ai_workflow_pack_execution_v1(
        pack_id=DPM_PROOF_PACK_PM_MEMO_EXECUTION.pack_id,
        workflow_surface=DPM_PROOF_PACK_PM_MEMO_EXECUTION.workflow_surface,
        correlation_id=correlation_id,
    )
    current: dict[str, Any] = payload
    for path_part in field_path[:-1]:
        current = current[path_part]
    current.pop(field_path[-1])

    with pytest.raises(HTTPException) as raised:
        validate_dpm_ai_workflow_execution(
            payload,
            upstream_status=200,
            correlation_id=correlation_id,
            expectation=DPM_PROOF_PACK_PM_MEMO_EXECUTION,
        )

    assert raised.value.status_code == status.HTTP_502_BAD_GATEWAY
    assert raised.value.detail["error_code"] == "AI_WORKFLOW_EXECUTION_CONTRACT_INVALID"


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
