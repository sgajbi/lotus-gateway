from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.contracts.advisor_brief import (
    AdvisorBriefWorkflowPackRun,
    AdvisorBriefWorkflowPackRunFinding,
    AdvisorBriefWorkflowPackTaskFlow,
    AdvisorBriefWorkflowPackTaskFlowHandoff,
    AdvisorBriefWorkflowPackTaskFlowLineage,
)
from app.services.advisory_client_protocols import AdvisorBriefAiClient

_ADVISOR_BRIEF_TASK_FLOW_LOOKUP_LIMIT = 100


def assert_advisor_brief_review_action_allowed(
    *,
    workflow_pack_run: AdvisorBriefWorkflowPackRun | None,
    run_id: str,
    action_type: str,
) -> None:
    if workflow_pack_run is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Advisor brief workflow-pack run `{run_id}` has no inspectable review posture; "
                "refresh the brief before recording a bounded review action."
            ),
        )
    allowed_actions = set(workflow_pack_run.allowed_review_actions)
    if action_type not in allowed_actions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Advisor brief workflow-pack run `{workflow_pack_run.run_id}` does not allow "
                f"review action `{action_type}` from runtime state "
                f"`{workflow_pack_run.runtime_state}` and review state "
                f"`{workflow_pack_run.review_state}`."
            ),
        )


async def load_advisor_brief_workflow_pack_run(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    ai_audit: dict[str, Any],
    correlation_id: str,
) -> AdvisorBriefWorkflowPackRun | None:
    run_id = resolve_advisor_brief_workflow_pack_run_id(ai_audit=ai_audit)
    if run_id is None:
        return None

    consumer_status, consumer_payload = await lotus_ai_client.get_workflow_pack_run_consumer_view(
        run_id=run_id,
        correlation_id=correlation_id,
    )
    if consumer_status != 200:
        return None

    (
        operator_status,
        operator_payload,
    ) = await lotus_ai_client.get_workflow_pack_run_operator_profile(
        run_id=run_id,
        correlation_id=correlation_id,
    )
    if operator_status != 200:
        return None

    review = _safe_dict(consumer_payload.get("review"))
    lineage = _safe_dict(consumer_payload.get("lineage"))
    findings = [
        finding
        for finding in (
            _parse_workflow_pack_run_finding(value=value)
            for value in _safe_list(operator_payload.get("findings"))
        )
        if finding is not None
    ]
    return AdvisorBriefWorkflowPackRun(
        run_id=_safe_str(operator_payload.get("run_id")) or run_id,
        runtime_state=_safe_str(operator_payload.get("runtime_state")) or "UNKNOWN",
        review_state=_safe_str(operator_payload.get("review_state")) or "UNKNOWN",
        allowed_review_actions=[
            action
            for action in (_safe_str(value) for value in _safe_list(review.get("allowed_actions")))
            if action is not None
        ],
        supportability_status=_safe_str(operator_payload.get("supportability_status")) or "UNKNOWN",
        review_pending=bool(operator_payload.get("review_pending")),
        superseded=bool(operator_payload.get("superseded")),
        workflow_authority_owner=_safe_str(lineage.get("workflow_authority_owner"))
        or "lotus-gateway",
        current_summary_note=_safe_str(operator_payload.get("current_summary_note"))
        or "Workflow-pack run posture is available without a current operator summary note.",
        replacement_run_id=_safe_str(operator_payload.get("replacement_run_id")),
        findings=findings,
    )


def resolve_advisor_brief_workflow_pack_run_id(*, ai_audit: dict[str, Any]) -> str | None:
    workflow_pack_run_id = _safe_str(ai_audit.get("workflow_pack_run_id"))
    if workflow_pack_run_id is not None:
        return workflow_pack_run_id
    request_id = _safe_str(ai_audit.get("request_id"))
    if request_id is None:
        return None
    return f"packrun_advisor_brief_{request_id}"


async def load_advisor_brief_workflow_pack_task_flow(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    ai_audit: dict[str, Any],
    correlation_id: str,
) -> AdvisorBriefWorkflowPackTaskFlow | None:
    run_id = resolve_advisor_brief_workflow_pack_run_id(ai_audit=ai_audit)
    if run_id is None:
        return None

    task_flow_status, task_flow_payload = await lotus_ai_client.list_workflow_pack_task_flows(
        correlation_id=correlation_id,
        workflow_pack_id="advisor_brief.pack",
        caller="lotus-gateway",
        workflow_surface="advisor-brief-workspace",
        limit=_ADVISOR_BRIEF_TASK_FLOW_LOOKUP_LIMIT,
    )
    if task_flow_status != 200:
        return None

    for value in _safe_list(task_flow_payload.get("task_flows")):
        task_flow = _parse_advisor_brief_workflow_pack_task_flow(value=value, run_id=run_id)
        if task_flow is not None:
            return task_flow
    return None


def _parse_advisor_brief_workflow_pack_task_flow(
    *,
    value: Any,
    run_id: str,
) -> AdvisorBriefWorkflowPackTaskFlow | None:
    item = _safe_dict(value)
    run_refs = [
        ref for ref in (_safe_str(value) for value in _safe_list(item.get("run_refs"))) if ref
    ]
    if run_id not in run_refs:
        return None

    task_flow_id = _safe_str(item.get("task_flow_id"))
    workflow_pack_id = _safe_str(item.get("workflow_pack_id"))
    version = _safe_str(item.get("workflow_pack_version")) or _safe_str(item.get("version"))
    flow_status = _safe_str(item.get("flow_status"))
    supportability_status = _safe_str(item.get("supportability_status"))
    updated_at = _safe_str(item.get("updated_at"))
    if task_flow_id is None:
        return None
    if workflow_pack_id is None:
        return None
    if version is None:
        return None
    if flow_status is None:
        return None
    if supportability_status is None:
        return None
    if updated_at is None:
        return None

    lineage = [
        lineage_item
        for lineage_item in (
            _parse_task_flow_lineage(value=value)
            for value in _safe_list(item.get("replacement_lineage"))
        )
        if lineage_item is not None
    ]
    handoff_refs = [
        handoff
        for handoff in (
            _parse_task_flow_handoff(value=value) for value in _safe_list(item.get("handoff_refs"))
        )
        if handoff is not None
    ]
    review_states = {
        str(key): str(value)
        for key, value in _safe_dict(item.get("review_states")).items()
        if key and value
    }
    return AdvisorBriefWorkflowPackTaskFlow(
        task_flow_id=task_flow_id,
        workflow_pack_id=workflow_pack_id,
        version=version,
        flow_status=flow_status,
        current_step_id=_safe_str(item.get("current_step_id")),
        run_refs=run_refs,
        review_states=review_states,
        supportability_status=supportability_status,
        replacement_lineage=lineage,
        handoff_refs=handoff_refs,
        updated_at=updated_at,
    )


def _parse_task_flow_lineage(*, value: Any) -> AdvisorBriefWorkflowPackTaskFlowLineage | None:
    item = _safe_dict(value)
    superseded_run_id = _safe_str(item.get("superseded_run_id"))
    replacement_run_id = _safe_str(item.get("replacement_run_id"))
    review_action_ref = _safe_str(item.get("review_action_ref"))
    reason = _safe_str(item.get("reason"))
    if (
        superseded_run_id is None
        or replacement_run_id is None
        or review_action_ref is None
        or reason is None
    ):
        return None
    return AdvisorBriefWorkflowPackTaskFlowLineage(
        superseded_run_id=superseded_run_id,
        replacement_run_id=replacement_run_id,
        review_action_ref=review_action_ref,
        reason=reason,
    )


def _parse_task_flow_handoff(*, value: Any) -> AdvisorBriefWorkflowPackTaskFlowHandoff | None:
    item = _safe_dict(value)
    handoff_id = _safe_str(item.get("handoff_id"))
    owner_service = _safe_str(item.get("owner_service"))
    status = _safe_str(item.get("status"))
    if handoff_id is None or owner_service is None or status is None:
        return None
    return AdvisorBriefWorkflowPackTaskFlowHandoff(
        handoff_id=handoff_id,
        owner_service=owner_service,
        status=status,
        domain_ref=_safe_str(item.get("domain_ref")),
    )


def _parse_workflow_pack_run_finding(*, value: Any) -> AdvisorBriefWorkflowPackRunFinding | None:
    item = _safe_dict(value)
    finding_id = _safe_str(item.get("finding_id"))
    severity = _safe_str(item.get("severity"))
    summary = _safe_str(item.get("summary"))
    if finding_id is None or severity is None or summary is None:
        return None
    return AdvisorBriefWorkflowPackRunFinding(
        finding_id=finding_id,
        severity=severity,
        summary=summary,
    )


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
