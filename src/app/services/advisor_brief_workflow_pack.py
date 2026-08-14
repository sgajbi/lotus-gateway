from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.contracts.advisor_brief import (
    AdvisorBriefWorkflowPackRun,
    AdvisorBriefWorkflowPackRunFinding,
    AdvisorBriefWorkflowPackTaskFlow,
)
from app.services.advisor_brief_client_protocols import AdvisorBriefAiClient
from app.services.advisor_brief_task_flow import parse_advisor_brief_workflow_pack_task_flow

_ADVISOR_BRIEF_TASK_FLOW_LOOKUP_LIMIT = 100


@dataclass(frozen=True)
class _WorkflowPackRunProfile:
    run_id: str
    consumer_payload: dict[str, Any]
    operator_payload: dict[str, Any]


@dataclass(frozen=True)
class _ReviewEvidence:
    latest_event_at: str | None = None
    latest_actor: str | None = None
    transition_count: int | None = None
    has_history: bool | None = None


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

    profile = await _load_workflow_pack_run_profile(
        lotus_ai_client=lotus_ai_client,
        run_id=run_id,
        correlation_id=correlation_id,
    )
    if profile is None:
        return None
    return _parse_workflow_pack_run_profile(profile=profile)


async def _load_workflow_pack_run_profile(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    run_id: str,
    correlation_id: str,
) -> _WorkflowPackRunProfile | None:
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
    return _WorkflowPackRunProfile(
        run_id=run_id,
        consumer_payload=consumer_payload,
        operator_payload=operator_payload,
    )


def _parse_workflow_pack_run_profile(
    *,
    profile: _WorkflowPackRunProfile,
) -> AdvisorBriefWorkflowPackRun:
    review = _safe_dict(profile.consumer_payload.get("review"))
    review_evidence = _parse_review_evidence(review)
    lineage = _safe_dict(profile.consumer_payload.get("lineage"))
    operator_payload = profile.operator_payload
    findings = [
        finding
        for finding in (
            _parse_workflow_pack_run_finding(value=value)
            for value in _safe_list(operator_payload.get("findings"))
        )
        if finding is not None
    ]
    return AdvisorBriefWorkflowPackRun(
        run_id=_safe_str(operator_payload.get("run_id")) or profile.run_id,
        runtime_state=_safe_str(operator_payload.get("runtime_state")) or "UNKNOWN",
        review_state=_safe_str(operator_payload.get("review_state")) or "UNKNOWN",
        latest_review_event_at=review_evidence.latest_event_at,
        latest_review_actor=review_evidence.latest_actor,
        review_transition_count=review_evidence.transition_count,
        has_review_history=review_evidence.has_history,
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
        task_flow = parse_advisor_brief_workflow_pack_task_flow(value=value, run_id=run_id)
        if task_flow is not None:
            return task_flow
    return None


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


def _safe_utc_timestamp(value: Any) -> str | None:
    timestamp = _safe_str(value)
    if (
        timestamp is None
        or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)",
            timestamp,
        )
        is None
    ):
        return None
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return timestamp if parsed.utcoffset() == timedelta(0) else None


def _parse_review_evidence(review: dict[str, Any]) -> _ReviewEvidence:
    raw_values = (
        review.get("latest_review_event_at"),
        review.get("latest_review_actor"),
        review.get("review_transition_count"),
        review.get("has_review_history"),
    )
    if all(value is None for value in raw_values):
        return _ReviewEvidence()

    latest_event_at = _safe_utc_timestamp(raw_values[0])
    latest_actor = _safe_str(raw_values[1])
    transition_count = _safe_non_negative_int(raw_values[2])
    has_history = _safe_bool(raw_values[3])

    if (
        has_history is True
        and latest_event_at is not None
        and latest_actor is not None
        and transition_count is not None
        and transition_count > 0
    ):
        return _ReviewEvidence(
            latest_event_at=latest_event_at,
            latest_actor=latest_actor,
            transition_count=transition_count,
            has_history=True,
        )
    if (
        has_history is False
        and latest_event_at is None
        and latest_actor is None
        and transition_count == 0
    ):
        return _ReviewEvidence(transition_count=0, has_history=False)
    return _ReviewEvidence()


def _safe_non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _safe_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
