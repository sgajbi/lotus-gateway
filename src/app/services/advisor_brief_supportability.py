from __future__ import annotations

from typing import Any

from app.contracts.advisor_brief import (
    AdvisorBriefAdvisorySupportability,
    AdvisorBriefAiSurfaceSupportability,
    AdvisorBriefAiSurfaceSupportabilityItem,
)
from app.services.advisory_client_protocols import AdvisorBriefAdviseClient, AdvisorBriefAiClient


async def load_advisory_supportability(
    *,
    advise_client: AdvisorBriefAdviseClient | None,
    correlation_id: str,
) -> AdvisorBriefAdvisorySupportability | None:
    if advise_client is None:
        return None
    status_code, payload = await advise_client.get_platform_capabilities(
        correlation_id=correlation_id
    )
    if status_code != 200:
        return None
    supportability = _safe_dict(payload.get("supportability"))
    if not supportability:
        return None
    return AdvisorBriefAdvisorySupportability(
        state=_safe_str(supportability.get("state")) or "unknown",
        reason=_safe_str(supportability.get("reason")),
        freshness_bucket=_safe_str(supportability.get("freshness_bucket")) or "unknown",
        dependency_count=_safe_int(supportability.get("dependency_count")),
        ready_dependency_count=_safe_int(supportability.get("ready_dependency_count")),
        degraded_dependency_count=_safe_int(supportability.get("degraded_dependency_count")),
        enabled_feature_count=_safe_int(supportability.get("enabled_feature_count")),
        ready_feature_count=_safe_int(supportability.get("ready_feature_count")),
    )


async def load_ai_surface_supportability(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    correlation_id: str,
) -> AdvisorBriefAiSurfaceSupportability | None:
    runtime_status, runtime_payload = await lotus_ai_client.get_observability_runtime_status(
        correlation_id=correlation_id
    )
    if runtime_status != 200:
        return None
    source = _safe_dict(runtime_payload.get("ai_surface_supportability"))
    if not source:
        return None
    return parse_ai_surface_supportability(source=source)


def parse_ai_surface_supportability(
    *,
    source: dict[str, Any],
) -> AdvisorBriefAiSurfaceSupportability:
    posture = _safe_str(source.get("posture")) or "unavailable"
    freshness = _safe_str(source.get("freshness")) or "unknown"
    return AdvisorBriefAiSurfaceSupportability(
        state=_normalize_ai_surface_supportability_state(posture),
        freshness_bucket=_normalize_ai_surface_freshness_bucket(freshness),
        posture=posture,
        freshness=freshness,
        metric_name=_safe_str(source.get("metric_name")) or "lotus_ai_surface_supportability_state",
        supported_surface_count=_safe_int(source.get("supported_surface_count")),
        executable_workflow_pack_count=_safe_int(source.get("executable_workflow_pack_count")),
        action_required_surface_count=_safe_int(source.get("action_required_surface_count")),
        unavailable_surface_count=_safe_int(source.get("unavailable_surface_count")),
        no_sensitive_content_telemetry=bool(source.get("no_sensitive_content_telemetry")),
        surfaces=[
            surface
            for surface in (
                _parse_ai_surface_supportability_item(value=value)
                for value in _safe_list(source.get("surfaces"))
            )
            if surface is not None
        ],
        status_summary=[
            summary
            for summary in (_safe_str(item) for item in _safe_list(source.get("status_summary")))
            if summary
        ],
    )


def _parse_ai_surface_supportability_item(
    *,
    value: Any,
) -> AdvisorBriefAiSurfaceSupportabilityItem | None:
    item = _safe_dict(value)
    surface_id = _safe_str(item.get("surface_id"))
    owning_service = _safe_str(item.get("owning_service"))
    workflow_authority_owner = _safe_str(item.get("workflow_authority_owner"))
    workflow_pack_ref = _safe_str(item.get("workflow_pack_ref"))
    supportability_status = _safe_str(item.get("supportability_status"))
    model_posture = _safe_str(item.get("model_posture"))
    if (
        surface_id is None
        or owning_service is None
        or workflow_authority_owner is None
        or workflow_pack_ref is None
        or supportability_status is None
        or model_posture is None
    ):
        return None
    return AdvisorBriefAiSurfaceSupportabilityItem(
        surface_id=surface_id,
        owning_service=owning_service,
        workflow_authority_owner=workflow_authority_owner,
        workflow_pack_ref=workflow_pack_ref,
        supportability_status=supportability_status,
        model_posture=model_posture,
        latest_ready_run_id=_safe_str(item.get("latest_ready_run_id")),
        latest_action_required_run_id=_safe_str(item.get("latest_action_required_run_id")),
        no_sensitive_content_telemetry=bool(item.get("no_sensitive_content_telemetry")),
        status_summary=[
            summary
            for summary in (_safe_str(item) for item in _safe_list(item.get("status_summary")))
            if summary
        ],
    )


def _normalize_ai_surface_supportability_state(posture: str) -> str:
    normalized = posture.strip().lower()
    if normalized == "healthy":
        return "ready"
    if normalized == "degraded":
        return "action_required"
    if normalized == "unavailable":
        return "unsupported"
    return "unknown"


def _normalize_ai_surface_freshness_bucket(freshness: str) -> str:
    normalized = freshness.strip().lower()
    if normalized in {"current", "fresh", "ready"}:
        return "fresh"
    if normalized == "stale":
        return "stale"
    return "unknown"


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    return 0
