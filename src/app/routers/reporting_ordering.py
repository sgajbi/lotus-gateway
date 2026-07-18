from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contracts.report_ordering import (
    ReportScopeSelection,
    WorkbenchReportOrderingResponse,
)
from app.contracts.report_ordering_examples import REPORT_ORDERING_RESPONSE_EXAMPLE
from app.middleware.correlation import correlation_id_var
from app.routers.reporting_context import ReportingCallerHeaderInputs
from app.services.reporting_service_provider import report_ordering_service

router = APIRouter(prefix="/api/v1/report-ordering", tags=["Reports"])


def _build_report_scope_selection(
    scope_type: Literal["portfolio", "client", "book"] | None,
    scope_id: str | None,
) -> ReportScopeSelection | None:
    if scope_type is None and scope_id is None:
        return None
    if scope_type is None or scope_id is None or not scope_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "invalid_report_ordering_scope",
                "message": "scopeType and scopeId must be supplied together.",
            },
        )
    return ReportScopeSelection(scopeType=scope_type, scopeId=scope_id.strip())


async def _get_report_ordering_options(
    *,
    selection: ReportScopeSelection | None,
    caller_headers: ReportingCallerHeaderInputs,
) -> WorkbenchReportOrderingResponse:
    return await report_ordering_service().get_ordering_options(
        selection=selection,
        caller_headers=caller_headers.as_headers(),
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/options",
    response_model=WorkbenchReportOrderingResponse,
    summary="Get report ordering options",
    description=(
        "Returns business report choices and caller-scope eligibility for the Workbench report "
        "ordering flow. Report configuration and output availability remain owned by Reporting; "
        "Gateway applies the trusted caller role and selected portfolio, client, or advisor-book "
        "scope. Ordering eligibility does not grant client distribution or prove document "
        "generation, archive completion, or whole-book membership."
    ),
    responses={
        200: {
            "description": "Source-backed report choices and scope eligibility.",
            "content": {"application/json": {"example": REPORT_ORDERING_RESPONSE_EXAMPLE}},
        },
        400: {"description": "Required trusted caller context is missing."},
        422: {"description": "The selected business scope is incomplete or invalid."},
    },
)
async def get_report_ordering_options(
    scope_type: Annotated[
        Literal["portfolio", "client", "book"] | None,
        Query(
            alias="scopeType",
            description="Optional business scope type selected in Workbench.",
        ),
    ] = None,
    scope_id: Annotated[
        str | None,
        Query(
            alias="scopeId",
            description="Identifier of the selected portfolio, client, or advisor book.",
        ),
    ] = None,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    portfolio_ids: Annotated[str | None, Header(alias="X-Caller-Portfolio-Ids")] = None,
    client_ids: Annotated[str | None, Header(alias="X-Caller-Client-Ids")] = None,
    book_ids: Annotated[str | None, Header(alias="X-Caller-Book-Ids")] = None,
) -> WorkbenchReportOrderingResponse:
    return await _get_report_ordering_options(
        selection=_build_report_scope_selection(scope_type, scope_id),
        caller_headers=ReportingCallerHeaderInputs(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
            portfolio_ids=portfolio_ids,
            client_ids=client_ids,
            book_ids=book_ids,
        ),
    )
