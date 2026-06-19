from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefNarrativeItem,
    AdvisorBriefStatus,
    AdvisorBriefTone,
)
from app.services.advisor_brief_ai_output import (
    extract_ai_recommended_actions,
    extract_ai_risks,
    extract_ai_summary,
    extract_ai_talking_points,
    safe_dict,
    safe_execution_detail,
)
from app.services.advisor_brief_source import (
    AdvisorBriefSourceContext,
    build_advisor_brief_ai_fact_bundle,
    build_advisor_brief_source_route,
    build_advisor_brief_summary_evidence_ref,
)

_TASK_ID = "explain.v1"
_EXPECTED_OUTPUT_LABEL = "EXPLANATION_ONLY"


@dataclass(frozen=True)
class AdvisorBriefNarrativeState:
    status: AdvisorBriefStatus
    summary: str
    talking_points: list[AdvisorBriefNarrativeItem]
    recommended_actions: list[AdvisorBriefActionItem]
    risks_and_exceptions: list[AdvisorBriefNarrativeItem]
    ai_audit: dict[str, Any]
    ai_evidence: dict[str, Any]


def build_advisor_brief_ai_task_request(
    *,
    correlation_id: str,
    source_context: AdvisorBriefSourceContext,
) -> dict[str, Any]:
    workspace = source_context.workspace
    return {
        "task_id": _TASK_ID,
        "input_mode": "STRUCTURED_CONTEXT",
        "caller": {
            "caller_app": "lotus-gateway",
            "correlation_id": correlation_id,
        },
        "context": {
            "summary": (
                f"Advisor brief context for portfolio {workspace.portfolio_id}, "
                f"{workspace.period} period, basis {workspace.detail_basis}."
            ),
            "payload": build_advisor_brief_ai_fact_bundle(
                source_context=source_context,
            ),
            "source_refs": source_context.source_refs,
        },
        "expected_output_label": _EXPECTED_OUTPUT_LABEL,
    }


def build_source_advisor_brief_narrative_state(
    *,
    source_context: AdvisorBriefSourceContext,
) -> AdvisorBriefNarrativeState:
    return AdvisorBriefNarrativeState(
        status=source_context.status,
        summary=source_context.summary,
        talking_points=source_context.talking_points,
        recommended_actions=source_context.recommended_actions,
        risks_and_exceptions=source_context.risks_and_exceptions,
        ai_audit=_normalize_ai_audit({}),
        ai_evidence={"descriptors": []},
    )


def build_ai_advisor_brief_narrative_state(
    *,
    source_context: AdvisorBriefSourceContext,
    narrative_state: AdvisorBriefNarrativeState,
    ai_status: int,
    ai_payload: dict[str, Any],
) -> AdvisorBriefNarrativeState:
    if ai_status != 200:
        return _build_ai_http_unavailable_narrative_state(
            source_context=source_context,
            narrative_state=narrative_state,
            ai_payload=ai_payload,
        )

    execution_payload = safe_dict(ai_payload.get("execution"))
    ai_audit = _normalize_ai_audit(safe_dict(execution_payload.get("audit")))
    ai_evidence = safe_dict(execution_payload.get("evidence")) or {"descriptors": []}
    if execution_payload.get("status") == "COMPLETED":
        return _build_completed_ai_advisor_brief_narrative_state(
            source_context=source_context,
            narrative_state=narrative_state,
            execution_payload=execution_payload,
            ai_audit=ai_audit,
            ai_evidence=ai_evidence,
        )

    return _build_ai_execution_unavailable_narrative_state(
        source_context=source_context,
        narrative_state=narrative_state,
        execution_payload=execution_payload,
        ai_audit=ai_audit,
        ai_evidence=ai_evidence,
    )


def safe_advisor_brief_error_detail(payload: dict[str, Any]) -> str:
    detail = payload.get("detail")
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return "lotus-ai task execution did not return a completed advisor brief."


def _build_completed_ai_advisor_brief_narrative_state(
    *,
    source_context: AdvisorBriefSourceContext,
    narrative_state: AdvisorBriefNarrativeState,
    execution_payload: dict[str, Any],
    ai_audit: dict[str, Any],
    ai_evidence: dict[str, Any],
) -> AdvisorBriefNarrativeState:
    structured_output = safe_dict(
        safe_dict(execution_payload.get("result")).get("structured_output")
    )
    route = build_advisor_brief_source_route(source_context=source_context)
    return replace(
        narrative_state,
        summary=extract_ai_summary(
            ai_payload=execution_payload,
            structured_output=structured_output,
        )
        or narrative_state.summary,
        talking_points=extract_ai_talking_points(
            structured_output=structured_output,
            route=route,
        )
        or narrative_state.talking_points,
        recommended_actions=extract_ai_recommended_actions(
            structured_output=structured_output,
            route=route,
        )
        or narrative_state.recommended_actions,
        risks_and_exceptions=extract_ai_risks(
            structured_output=structured_output,
            route=route,
        )
        or narrative_state.risks_and_exceptions,
        ai_audit=ai_audit,
        ai_evidence=ai_evidence,
    )


def _build_ai_execution_unavailable_narrative_state(
    *,
    source_context: AdvisorBriefSourceContext,
    narrative_state: AdvisorBriefNarrativeState,
    execution_payload: dict[str, Any],
    ai_audit: dict[str, Any],
    ai_evidence: dict[str, Any],
) -> AdvisorBriefNarrativeState:
    detail = safe_execution_detail(execution_payload) or (
        "Source-backed metrics remain available for manual review and client prep."
    )
    return _with_ai_unavailable_risk(
        source_context=source_context,
        narrative_state=narrative_state,
        detail=detail,
        ai_audit=ai_audit,
        ai_evidence=ai_evidence,
    )


def _build_ai_http_unavailable_narrative_state(
    *,
    source_context: AdvisorBriefSourceContext,
    narrative_state: AdvisorBriefNarrativeState,
    ai_payload: dict[str, Any],
) -> AdvisorBriefNarrativeState:
    ai_audit = _normalize_ai_audit(
        {
            "task_id": _TASK_ID,
            "output_label": _EXPECTED_OUTPUT_LABEL,
            "provider_mode": "unavailable",
            "detail": safe_advisor_brief_error_detail(ai_payload),
        }
    )
    return _with_ai_unavailable_risk(
        source_context=source_context,
        narrative_state=narrative_state,
        detail="Source-backed metrics remain available for manual review and client prep.",
        ai_audit=ai_audit,
        ai_evidence={"descriptors": []},
    )


def _with_ai_unavailable_risk(
    *,
    source_context: AdvisorBriefSourceContext,
    narrative_state: AdvisorBriefNarrativeState,
    detail: str,
    ai_audit: dict[str, Any],
    ai_evidence: dict[str, Any],
) -> AdvisorBriefNarrativeState:
    return replace(
        narrative_state,
        status=AdvisorBriefStatus.PARTIAL,
        risks_and_exceptions=[
            *narrative_state.risks_and_exceptions,
            _build_ai_unavailable_risk(source_context=source_context, detail=detail),
        ],
        ai_audit=ai_audit,
        ai_evidence=ai_evidence,
    )


def _build_ai_unavailable_risk(
    *,
    source_context: AdvisorBriefSourceContext,
    detail: str,
) -> AdvisorBriefNarrativeItem:
    return AdvisorBriefNarrativeItem(
        headline="AI narrative generation is unavailable.",
        detail=detail,
        tone=AdvisorBriefTone.WARNING,
        evidence_refs=[
            build_advisor_brief_summary_evidence_ref(
                label="Advisor Brief",
                value="Unavailable",
                source_context=source_context,
            )
        ],
    )


def _normalize_ai_audit(audit: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(audit)
    normalized.setdefault("task_id", _TASK_ID)
    normalized.setdefault("output_label", _EXPECTED_OUTPUT_LABEL)
    normalized.setdefault("provider_mode", "unknown")
    normalized.setdefault("provider_id", None)
    normalized.setdefault("adapter_kind", None)
    normalized.setdefault("model_id", None)
    normalized.setdefault("generated_at", None)
    normalized.setdefault("stubbed", True)
    normalized.setdefault("source_refs", [])
    return normalized
