"""Primary Advisor Book workspace route: one dense composition for the trusted book."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse
from app.contracts.advisor_book_workspace import AdvisorBookWorkspaceResponse
from app.contracts.advisor_book_workspace_examples import (
    ADVISOR_BOOK_WORKSPACE_RESPONSE_EXAMPLE,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_book_request import (
    AdvisorBookCallerHeaders,
    advisor_book_caller_headers,
    advisor_book_error_response,
    advisor_book_source_error_response,
    advisor_book_summary_query,
)
from app.routers.advisor_cockpit_request import (
    AdvisorCockpitCallerHeaders,
    advisor_cockpit_caller_headers,
    authorize_advisor_cockpit_request,
    build_advisor_cockpit_caller,
)
from app.services.advisor_book_access_policy import (
    AdvisorBookCallerContextError,
    require_advisor_book_caller_context,
)
from app.services.advisor_book_service_errors import AdvisorBookServiceError
from app.services.advisor_book_workspace_facts import AdviseScope, AdviseScopeUnavailable
from app.services.advisor_book_workspace_service_provider import (
    advisor_book_workspace_service,
)
from app.services.advisor_cockpit_access_policy import (
    ADVISOR_COCKPIT_READ_CAPABILITY,
    AdvisorCockpitAccessError,
)

router = APIRouter(prefix="/api/v1/advisor-book", tags=["advisor-book"])

_SOURCE_UNAVAILABLE_MESSAGE = (
    "The advisor-book membership source is unavailable or could not be safely verified."
)


def _resolve_advise_scope(headers: AdvisorCockpitCallerHeaders) -> AdviseScope:
    """Admit the optional Advise advisor scope, degrading instead of failing.

    The workspace's action fact is optional enrichment: a caller without any Advise
    context, with an invalid or unauthorized context, or with a non-advisor scope
    still receives the full value composition — the action fact block states why it
    is unavailable instead of the route rejecting the request.
    """

    if (
        headers.legal_entity_code is None
        and headers.principal_status is None
        and headers.authorized_advisor_id is None
        and headers.authorized_portfolio_id is None
    ):
        return AdviseScopeUnavailable("advise_scope_not_presented")
    try:
        caller = build_advisor_cockpit_caller(headers)
        authorize_advisor_cockpit_request(
            caller,
            capability=ADVISOR_COCKPIT_READ_CAPABILITY,
            portfolio_id=None,
        )
    except (AdvisorCockpitAccessError, HTTPException):
        return AdviseScopeUnavailable("advise_scope_invalid")
    # The action feed's advertised scope basis is exactly one advisor's Advise feed:
    # a portfolio-scoped entitlement cannot cover the whole book and an unscoped
    # principal could receive a feed wider than one advisor's book.
    if caller.authorized_portfolio_id is None and caller.authorized_advisor_id is not None:
        return caller
    return AdviseScopeUnavailable("advise_scope_not_advisor")


async def _get_advisor_book_workspace(
    *,
    query: tuple[date, str],
    caller_headers: AdvisorBookCallerHeaders,
    cockpit_headers: AdvisorCockpitCallerHeaders,
) -> AdvisorBookWorkspaceResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    as_of_date, reporting_currency = query
    try:
        book_caller = require_advisor_book_caller_context(
            actor_id=caller_headers.actor_id,
            caller_application=caller_headers.caller_application,
            tenant_id=caller_headers.tenant_id,
            region=caller_headers.region,
            booking_center_code=caller_headers.booking_center_code,
            role=caller_headers.role,
            capabilities=caller_headers.capabilities,
        )
        return await advisor_book_workspace_service().get_workspace(
            book_caller=book_caller,
            advise_scope=_resolve_advise_scope(cockpit_headers),
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            correlation_id=correlation_id,
        )
    except HTTPException as exc:
        return advisor_book_source_error_response(
            exc,
            correlation_id=correlation_id,
            outage_code="advisor_book_workspace_source_unavailable",
            outage_message=_SOURCE_UNAVAILABLE_MESSAGE,
        )
    except (AdvisorBookCallerContextError, AdvisorBookServiceError) as exc:
        return advisor_book_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
        )


@router.get(
    "/workspace",
    response_model=AdvisorBookWorkspaceResponse,
    summary="Get the advisor-book workspace",
    description=(
        "Returns the primary Advisor Book composition: membership is resolved exactly "
        "once from Core for the requested business date, the cohort and its provenance "
        "are frozen, and Core bulk value facts plus lotus-advise action-item facts are "
        "composed against exactly that cohort under one elapsed composition deadline. "
        "Every cohort member is a row; a degraded enrichment source degrades only its "
        "own fact block with a bounded reason and never removes a row. The Advise "
        "action fact is admitted under the caller's optional advisor scope and the two "
        "trust scopes are intersected on portfolio identity only; an absent or "
        "non-advisor Advise scope leaves the action fact explicitly unavailable rather "
        "than failing the request. Action items are current-state workflow evidence: a "
        "historical membership date never implies historical action evidence. Only an "
        "unresolvable membership cohort is fatal."
    ),
    responses={
        200: {
            "description": "The dense workspace composition for the advisor's own book.",
            "content": {"application/json": {"example": ADVISOR_BOOK_WORKSPACE_RESPONSE_EXAMPLE}},
        },
        400: {
            "model": AdvisorBookErrorResponse,
            "description": "Required trusted caller context is missing or invalid.",
        },
        403: {
            "model": AdvisorBookErrorResponse,
            "description": "The caller is not entitled to the advisor book.",
        },
        422: {"description": "A business-date or reporting-currency input is invalid."},
        502: {
            "model": AdvisorBookErrorResponse,
            "description": "The membership source is unavailable or unverified.",
        },
        504: {
            "model": AdvisorBookErrorResponse,
            "description": "The composition deadline was exhausted before membership resolved.",
        },
    },
)
async def get_advisor_book_workspace(
    query: Annotated[tuple[date, str], Depends(advisor_book_summary_query)],
    caller_headers: Annotated[AdvisorBookCallerHeaders, Depends(advisor_book_caller_headers)],
    cockpit_headers: Annotated[
        AdvisorCockpitCallerHeaders, Depends(advisor_cockpit_caller_headers)
    ],
) -> AdvisorBookWorkspaceResponse | JSONResponse:
    return await _get_advisor_book_workspace(
        query=query,
        caller_headers=caller_headers,
        cockpit_headers=cockpit_headers,
    )
