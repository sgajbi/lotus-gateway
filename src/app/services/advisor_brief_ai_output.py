from typing import Any

from pydantic import ValidationError

from app.contracts.advisor_brief import (
    AdvisorBriefActionItem,
    AdvisorBriefEvidenceRef,
    AdvisorBriefNarrativeItem,
    AdvisorBriefTone,
)
from app.contracts.ai_output_validation import AiOutputValidation

ADVISOR_BRIEF_TASK_ID = "explain.v1"
ADVISOR_BRIEF_OUTPUT_LABEL = "EXPLANATION_ONLY"


def parse_output_validation(execution_payload: dict[str, Any]) -> AiOutputValidation | None:
    """Typed verdict from the source execution, or None when absent/undecodable.

    None fails closed in ai_output_displayable: an execution without a provable
    verdict never becomes displayable narrative content.
    """

    raw = execution_payload.get("output_validation")
    if not isinstance(raw, dict):
        return None
    try:
        return AiOutputValidation.model_validate(raw)
    except ValidationError:
        return None


def extract_ai_summary(
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


def extract_ai_talking_points(
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


def extract_ai_risks(
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


def extract_ai_recommended_actions(
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


def safe_dict(value: Any) -> dict[str, Any]:
    return _safe_dict(value)


def safe_execution_detail(payload: dict[str, Any]) -> str | None:
    result = _safe_dict(payload.get("result"))
    message = _safe_str(result.get("message"))
    if message is not None:
        return message
    audit = _safe_dict(payload.get("audit"))
    detail = _safe_str(audit.get("detail"))
    if detail is not None:
        return detail
    return None


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


def normalize_ai_audit(audit: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(audit)
    normalized.setdefault("task_id", ADVISOR_BRIEF_TASK_ID)
    normalized.setdefault("output_label", ADVISOR_BRIEF_OUTPUT_LABEL)
    normalized.setdefault("provider_mode", "unknown")
    normalized.setdefault("provider_id", None)
    normalized.setdefault("adapter_kind", None)
    normalized.setdefault("model_id", None)
    normalized.setdefault("generated_at", None)
    normalized.setdefault("stubbed", True)
    normalized.setdefault("source_refs", [])
    return normalized


def unavailable_provider_audit() -> dict[str, Any]:
    return normalize_ai_audit(
        {
            "provider_mode": "unavailable",
            "provider_id": None,
            "adapter_kind": None,
            "model_id": None,
            "generated_at": None,
            "stubbed": True,
            "detail": "AI provider provenance could not be verified.",
            "source_refs": [],
        }
    )
