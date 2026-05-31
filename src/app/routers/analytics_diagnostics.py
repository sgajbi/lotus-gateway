from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, status

from app.contracts.analytics_diagnostics import (
    ANALYTICS_DIAGNOSTICS_RESPONSE_EXAMPLE,
    AnalyticsDiagnosticsResponse,
)
from app.observability.analytics_ui import (
    emit_gateway_protected_diagnostics_audit_log,
)
from app.services.analytics_diagnostics_service import (
    is_authorized_operator_role,
    is_safe_support_reference,
    resolve_support_reference,
)
from app.services.caller_context import caller_context_headers

logger = logging.getLogger("analytics_ui.gateway")

router = APIRouter(prefix="/api/v1/analytics-ui", tags=["Analytics Diagnostics"])


def _validate_diagnostics_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> None:
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


def _raise_for_unauthorized_diagnostics_role(role: str | None) -> None:
    if is_authorized_operator_role(role):
        return
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


def _raise_for_unsafe_support_reference(support_reference: str) -> None:
    if is_safe_support_reference(support_reference):
        return
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


async def _lookup_analytics_diagnostics(
    *,
    support_reference: str,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> AnalyticsDiagnosticsResponse:
    _validate_diagnostics_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
    _raise_for_unauthorized_diagnostics_role(role)
    _raise_for_unsafe_support_reference(support_reference)
    response = resolve_support_reference(support_reference)
    emit_gateway_protected_diagnostics_audit_log(
        logger=logger,
        status_code=status.HTTP_200_OK,
        reason="lookup_succeeded",
    )
    return response


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
    return await _lookup_analytics_diagnostics(
        support_reference=support_reference,
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
