from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from app.services.advisor_cockpit_access_policy import (
    AdvisorCockpitAccessError,
    AdvisorCockpitCallerContext,
    require_advisor_cockpit_caller_context,
    require_advisor_cockpit_capability,
    require_advisor_cockpit_portfolio_scope,
)


def advisor_cockpit_caller_context(
    request: Request,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    legal_entity_code: Annotated[str | None, Header(alias="X-Legal-Entity-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
    principal_status: Annotated[str | None, Header(alias="X-Principal-Status")] = None,
    authorized_advisor_id: Annotated[str | None, Header(alias="X-Authorized-Advisor-Id")] = None,
    authorized_portfolio_id: Annotated[
        str | None, Header(alias="X-Authorized-Portfolio-Id")
    ] = None,
) -> AdvisorCockpitCallerContext:
    if "advisor_id" in request.query_params or "role" in request.query_params:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "advisor_cockpit_authority_query_not_supported",
                "message": "Advisor identity and role are derived from trusted caller context.",
            },
        )
    try:
        return require_advisor_cockpit_caller_context(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            legal_entity_code=legal_entity_code,
            role=role,
            capabilities=capabilities,
            principal_status=principal_status,
            authorized_advisor_id=authorized_advisor_id,
            authorized_portfolio_id=authorized_portfolio_id,
        )
    except AdvisorCockpitAccessError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc


AdvisorCockpitCaller = Annotated[
    AdvisorCockpitCallerContext,
    Depends(advisor_cockpit_caller_context),
]


def authorize_advisor_cockpit_request(
    caller: AdvisorCockpitCallerContext,
    *,
    capability: str,
    portfolio_id: str | None,
    portfolio_required: bool = False,
) -> str | None:
    try:
        require_advisor_cockpit_capability(caller, capability)
        return require_advisor_cockpit_portfolio_scope(
            caller,
            portfolio_id,
            required=portfolio_required,
        )
    except AdvisorCockpitAccessError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
