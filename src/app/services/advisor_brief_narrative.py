from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefStatus,
    AdvisorBriefTone,
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

    execution_payload = _safe_dict(ai_payload.get("execution"))
    ai_audit = _normalize_ai_audit(_safe_dict(execution_payload.get("audit")))
    ai_evidence = _safe_dict(execution_payload.get("evidence")) or {"descriptors": []}
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
    structured_output = _safe_dict(
        _safe_dict(execution_payload.get("result")).get("structured_output")
    )
    route = build_advisor_brief_source_route(source_context=source_context)
    return replace(
        narrative_state,
        summary=_extract_ai_summary(
            ai_payload=execution_payload,
            structured_output=structured_output,
        )
        or narrative_state.summary,
        talking_points=_extract_ai_talking_points(
            structured_output=structured_output,
            route=route,
        )
        or narrative_state.talking_points,
        recommended_actions=_extract_ai_recommended_actions(
            structured_output=structured_output,
            route=route,
        )
        or narrative_state.recommended_actions,
        risks_and_exceptions=_extract_ai_risks(
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
    detail = _safe_execution_detail(execution_payload) or (
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


def _extract_ai_summary(
    *,
    ai_payload: dict[str, Any],
    structured_output: dict[str, Any] | None = None,
) -> str | None:
    output_payload = structured_output or _safe_dict(
        _safe_dict(ai_payload.get("result")).get("structured_output")
    )
    summary = output_payload.get("grounded_summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()
    result = _safe_dict(ai_payload.get("result"))
    message = result.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None


def _extract_ai_talking_points(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefNarrativeItem]:
    return [
        item
        for item in (
            _parse_ai_narrative_item(value=value, route=route, default_mode="summary")
            for value in _safe_list(structured_output.get("talking_points"))
        )
        if item is not None
    ]


def _extract_ai_risks(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefNarrativeItem]:
    return [
        item
        for item in (
            _parse_ai_narrative_item(value=value, route=route, default_mode="analysis")
            for value in _safe_list(structured_output.get("risks_and_exceptions"))
        )
        if item is not None
    ]


def _extract_ai_recommended_actions(
    *,
    structured_output: dict[str, Any],
    route: str,
) -> list[AdvisorBriefActionItem]:
    actions: list[AdvisorBriefActionItem] = []
    for value in _safe_list(structured_output.get("recommended_actions")):
        item = _safe_dict(value)
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            continue
        actions.append(
            AdvisorBriefActionItem(
                label=label.strip(),
                target_mode=_infer_target_mode_from_text(label),
                route=route,
            )
        )
    return actions


def _parse_ai_narrative_item(
    *,
    value: Any,
    route: str,
    default_mode: str,
) -> AdvisorBriefNarrativeItem | None:
    item = _safe_dict(value)
    headline = item.get("headline")
    detail = item.get("detail")
    if not isinstance(headline, str) or not headline.strip():
        return None
    if not isinstance(detail, str) or not detail.strip():
        return None
    tone = _normalize_narrative_tone(item.get("tone"))
    evidence_refs = [
        ref
        for ref in (
            _parse_ai_evidence_ref(value=ref_value, route=route, default_mode=default_mode)
            for ref_value in _safe_list(item.get("evidence_refs"))
        )
        if ref is not None
    ]
    if not evidence_refs:
        evidence_refs = [
            AdvisorBriefEvidenceRef(
                metric_label="Advisor Brief",
                metric_value="Source-Grounded",
                source_surface="performance.advisor_brief",
                target_mode=default_mode,
                route=route,
            )
        ]
    return AdvisorBriefNarrativeItem(
        headline=headline.strip(),
        detail=detail.strip(),
        tone=tone,
        evidence_refs=evidence_refs,
    )


def _parse_ai_evidence_ref(
    *,
    value: Any,
    route: str,
    default_mode: str,
) -> AdvisorBriefEvidenceRef | None:
    item = _safe_dict(value)
    metric_label = item.get("metric_label")
    metric_value = item.get("metric_value")
    if not isinstance(metric_label, str) or not metric_label.strip():
        return None
    if not isinstance(metric_value, str) or not metric_value.strip():
        return None
    source_ref = _safe_str(item.get("source_ref")) or _safe_str(item.get("source_surface"))
    source_surface = (
        _infer_source_surface(source_ref) if source_ref else "performance.advisor_brief"
    )
    return AdvisorBriefEvidenceRef(
        metric_label=metric_label.strip(),
        metric_value=metric_value.strip(),
        source_surface=source_surface,
        target_mode=_infer_target_mode(source_surface=source_surface, default_mode=default_mode),
        route=route,
    )


def _normalize_narrative_tone(value: Any) -> AdvisorBriefTone:
    if value == AdvisorBriefTone.POSITIVE.value:
        return AdvisorBriefTone.POSITIVE
    if value == AdvisorBriefTone.WARNING.value:
        return AdvisorBriefTone.WARNING
    return AdvisorBriefTone.NEUTRAL


def _infer_target_mode(*, source_surface: str, default_mode: str) -> str:
    return "summary" if source_surface == "performance.return_path" else default_mode


def _infer_target_mode_from_text(label: str) -> str:
    normalized = label.strip().lower()
    if "return" in normalized:
        return "summary"
    return "analysis"


def _infer_source_surface(source_ref: str | None) -> str:
    if not source_ref:
        return "performance.advisor_brief"
    normalized = source_ref.lower()
    if "performance-summary" in normalized:
        return "performance.return_path"
    if "performance-details" in normalized or "contribution" in normalized:
        return "performance.contribution"
    if "benchmark" in normalized or "attribution" in normalized:
        return "performance.attribution"
    return "performance.advisor_brief"


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_execution_detail(payload: dict[str, Any]) -> str | None:
    result = _safe_dict(payload.get("result"))
    message = _safe_str(result.get("message"))
    if message is not None:
        return message
    audit = _safe_dict(payload.get("audit"))
    detail = _safe_str(audit.get("detail"))
    if detail is not None:
        return detail
    return None
