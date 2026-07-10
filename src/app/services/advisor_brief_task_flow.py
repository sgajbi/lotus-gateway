from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.contracts.advisor_brief import (
    AdvisorBriefWorkflowPackTaskFlow,
    AdvisorBriefWorkflowPackTaskFlowHandoff,
    AdvisorBriefWorkflowPackTaskFlowLineage,
)


@dataclass(frozen=True)
class TaskFlowRequiredFields:
    task_flow_id: str
    workflow_pack_id: str
    version: str
    flow_status: str
    supportability_status: str
    updated_at: str


def parse_advisor_brief_workflow_pack_task_flow(
    *,
    value: Any,
    run_id: str,
) -> AdvisorBriefWorkflowPackTaskFlow | None:
    item = _safe_dict(value)
    run_refs = _parse_task_flow_run_refs(item=item)
    if run_id not in run_refs:
        return None

    required_fields = _parse_task_flow_required_fields(item=item)
    if required_fields is None:
        return None

    return AdvisorBriefWorkflowPackTaskFlow(
        task_flow_id=required_fields.task_flow_id,
        workflow_pack_id=required_fields.workflow_pack_id,
        version=required_fields.version,
        flow_status=required_fields.flow_status,
        current_step_id=_safe_str(item.get("current_step_id")),
        run_refs=run_refs,
        review_states=_parse_task_flow_review_states(item=item),
        supportability_status=required_fields.supportability_status,
        replacement_lineage=_parse_task_flow_lineage_items(item=item),
        handoff_refs=_parse_task_flow_handoff_refs(item=item),
        updated_at=required_fields.updated_at,
    )


def _parse_task_flow_run_refs(*, item: dict[str, Any]) -> list[str]:
    return [ref for ref in (_safe_str(value) for value in _safe_list(item.get("run_refs"))) if ref]


def _parse_task_flow_required_fields(
    *,
    item: dict[str, Any],
) -> TaskFlowRequiredFields | None:
    task_flow_id = _safe_str(item.get("task_flow_id"))
    workflow_pack_id = _safe_str(item.get("workflow_pack_id"))
    version = _safe_str(item.get("workflow_pack_version")) or _safe_str(item.get("version"))
    flow_status = _safe_str(item.get("flow_status"))
    supportability_status = _safe_str(item.get("supportability_status"))
    updated_at = _safe_str(item.get("updated_at"))
    if (
        task_flow_id is None
        or workflow_pack_id is None
        or version is None
        or flow_status is None
        or supportability_status is None
        or updated_at is None
    ):
        return None
    return TaskFlowRequiredFields(
        task_flow_id=task_flow_id,
        workflow_pack_id=workflow_pack_id,
        version=version,
        flow_status=flow_status,
        supportability_status=supportability_status,
        updated_at=updated_at,
    )


def _parse_task_flow_review_states(*, item: dict[str, Any]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in _safe_dict(item.get("review_states")).items()
        if key and value
    }


def _parse_task_flow_lineage_items(
    *,
    item: dict[str, Any],
) -> list[AdvisorBriefWorkflowPackTaskFlowLineage]:
    return [
        lineage_item
        for lineage_item in (
            _parse_task_flow_lineage(value=value)
            for value in _safe_list(item.get("replacement_lineage"))
        )
        if lineage_item is not None
    ]


def _parse_task_flow_handoff_refs(
    *,
    item: dict[str, Any],
) -> list[AdvisorBriefWorkflowPackTaskFlowHandoff]:
    return [
        handoff
        for handoff in (
            _parse_task_flow_handoff(value=value) for value in _safe_list(item.get("handoff_refs"))
        )
        if handoff is not None
    ]


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


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
