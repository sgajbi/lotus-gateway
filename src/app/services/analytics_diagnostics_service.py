from __future__ import annotations

import re

from app.contracts.analytics_diagnostics import AnalyticsDiagnosticsResponse
from app.observability.analytics_ui import ANALYTICS_UI_FORBIDDEN_FIELDS

_SAFE_SUPPORT_REFERENCE = re.compile(r"^gdiag-[A-Za-z0-9][A-Za-z0-9_.:-]{1,121}$")
_AUTHORIZED_OPERATOR_ROLES = {
    "admin",
    "ops",
    "operations",
    "operator",
    "support",
    "support_operator",
}


def is_authorized_operator_role(role: str | None) -> bool:
    normalized_role = (role or "").strip().lower().replace("-", "_")
    return normalized_role in _AUTHORIZED_OPERATOR_ROLES


def is_safe_support_reference(support_reference: str) -> bool:
    return _SAFE_SUPPORT_REFERENCE.fullmatch(support_reference) is not None


def resolve_support_reference(support_reference: str) -> AnalyticsDiagnosticsResponse:
    normalized = support_reference.lower()
    if "risk" in normalized:
        panel = "risk-summary"
        operation = "analytics.risk.calculate"
        service = "lotus-risk"
    elif "performance" in normalized:
        panel = "performance-summary"
        operation = "performance.workspace-summary"
        service = "lotus-performance"
    else:
        panel = "unknown"
        operation = "analytics-ui.lookup"
        service = "unknown"

    if "permission" in normalized or "denied" in normalized or "blocked" in normalized:
        supportability_state = "permission_blocked"
        reason = "upstream_authorization_denied"
    elif "degraded" in normalized or "partial" in normalized:
        supportability_state = "degraded"
        reason = "upstream_partial_or_degraded"
    else:
        supportability_state = "ready"
        reason = "safe_reference_resolved"

    return AnalyticsDiagnosticsResponse(
        supportReference=support_reference,
        panel=panel,
        supportabilityState=supportability_state,
        safeDimensions={
            "operation": operation,
            "service": service,
            "state": supportability_state,
            "reason": reason,
        },
        operatorGuidance=_operator_guidance(supportability_state),
        forbiddenFields=sorted(ANALYTICS_UI_FORBIDDEN_FIELDS),
    )


def _operator_guidance(supportability_state: str) -> list[str]:
    if supportability_state == "permission_blocked":
        return [
            "Confirm caller entitlement and region posture in the authoritative upstream service.",
            (
                "Use protected operational evidence for correlation lookup; do not add identifiers "
                "to dashboard labels."
            ),
        ]
    if supportability_state == "degraded":
        return [
            (
                "Check upstream service health and partial-failure posture for the safe operation "
                "dimension."
            ),
            "Escalate with bounded service, operation, state, and reason only.",
        ]
    return [
        (
            "Use the safe dimensions to locate the relevant analytics panel and upstream service "
            "posture."
        ),
        (
            "Keep raw request, response, trace, correlation, and client identifiers out of "
            "analytics UI telemetry."
        ),
    ]
