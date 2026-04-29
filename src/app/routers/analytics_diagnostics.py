from __future__ import annotations

import logging
import re
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, status

from app.contracts.analytics_diagnostics import (
    ANALYTICS_DIAGNOSTICS_RESPONSE_EXAMPLE,
    AnalyticsDiagnosticsResponse,
)
from app.observability.analytics_ui import (
    ANALYTICS_UI_FORBIDDEN_FIELDS,
    emit_gateway_protected_diagnostics_audit_log,
)
from app.services.caller_context import caller_context_headers

logger = logging.getLogger("analytics_ui.gateway")

router = APIRouter(prefix="/api/v1/analytics-ui", tags=["Analytics Diagnostics"])

_SAFE_SUPPORT_REFERENCE = re.compile(r"^gdiag-[A-Za-z0-9][A-Za-z0-9_.:-]{1,121}$")
_AUTHORIZED_OPERATOR_ROLES = {
    "admin",
    "ops",
    "operations",
    "operator",
    "support",
    "support_operator",
}


@router.get(
    "/diagnostics/{support_reference}",
    response_model=AnalyticsDiagnosticsResponse,
    summary="Resolve protected analytics diagnostics posture",
    description=(
        "Resolve an opaque analytics UI support reference into product-safe operator posture. "
        "This endpoint requires governed caller context plus an operator role and returns only "
        "bounded dimensions, supportability state, and runbook guidance. It must not expose raw "
        "portfolio, client, holding, trace, correlation, request, response, or entitlement data."
    ),
    openapi_extra={
        "responses": {
            "200": {
                "content": {"application/json": {"example": ANALYTICS_DIAGNOSTICS_RESPONSE_EXAMPLE}}
            }
        }
    },
)
async def lookup_analytics_diagnostics(
    support_reference: Annotated[
        str,
        Path(
            description=(
                "Opaque safe analytics support reference. Raw portfolio, client, holding, "
                "trace, correlation, request, response, and entitlement identifiers are rejected."
            ),
            examples=["gdiag-risk-summary-permission-blocked"],
        ),
    ],
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> AnalyticsDiagnosticsResponse:
    try:
        caller_context_headers(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
        )
    except HTTPException:
        emit_gateway_protected_diagnostics_audit_log(
            logger=logger,
            status_code=status.HTTP_400_BAD_REQUEST,
            reason="missing_caller_context",
        )
        raise

    normalized_role = (role or "").strip().lower().replace("-", "_")
    if normalized_role not in _AUTHORIZED_OPERATOR_ROLES:
        emit_gateway_protected_diagnostics_audit_log(
            logger=logger,
            status_code=status.HTTP_403_FORBIDDEN,
            reason="operator_role_required",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "operator_role_required",
                "message": "Analytics diagnostics lookup requires an operator support role.",
            },
        )

    if not _SAFE_SUPPORT_REFERENCE.fullmatch(support_reference):
        emit_gateway_protected_diagnostics_audit_log(
            logger=logger,
            status_code=status.HTTP_400_BAD_REQUEST,
            reason="invalid_support_reference",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_support_reference",
                "message": "Support reference must be opaque and product-safe.",
            },
        )

    response = _resolve_support_reference(support_reference)
    emit_gateway_protected_diagnostics_audit_log(
        logger=logger,
        status_code=status.HTTP_200_OK,
        reason="lookup_succeeded",
    )
    return response


def _resolve_support_reference(support_reference: str) -> AnalyticsDiagnosticsResponse:
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
