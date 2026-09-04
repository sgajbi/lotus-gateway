"""Advisor-book attention route: Advise-owned action counts for the trusted book."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse
from app.contracts.advisor_book_attention import AdvisorBookAttentionResponse
from app.contracts.advisor_book_attention_examples import ADVISOR_BOOK_ATTENTION_RESPONSE_EXAMPLE
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_book_request import (
    AdvisorBookCallerHeaders,
    advisor_book_attention_query,
    advisor_book_caller_headers,
    advisor_book_error_response,
)
from app.routers.advisor_cockpit_request import (
    advisor_cockpit_caller_context,
    authorize_advisor_cockpit_request,
)
from app.services.advisor_book_access_policy import (
    AdvisorBookCallerContextError,
    require_advisor_book_caller_context,
)
from app.services.advisor_book_attention_service_provider import advisor_book_attention_service
from app.services.advisor_book_service import AdvisorBookServiceError
from app.services.advisor_cockpit_access_policy import (
    ADVISOR_COCKPIT_READ_CAPABILITY,
    AdvisorCockpitCallerContext,
)

router = APIRouter(prefix="/api/v1/advisor-book", tags=["advisor-book"])


async def _get_advisor_book_attention(
    *,
    as_of_date: date,
    caller_headers: AdvisorBookCallerHeaders,
    cockpit_caller: AdvisorCockpitCallerContext,
) -> AdvisorBookAttentionResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        rejection = _reject_non_advisor_advise_scope(cockpit_caller, correlation_id)
        if rejection is not None:
            return rejection
        book_caller = require_advisor_book_caller_context(
            actor_id=caller_headers.actor_id,
            caller_application=caller_headers.caller_application,
            tenant_id=caller_headers.tenant_id,
            region=caller_headers.region,
            booking_center_code=caller_headers.booking_center_code,
            role=caller_headers.role,
            capabilities=caller_headers.capabilities,
        )
        return await advisor_book_attention_service().get_attention(
            book_caller=book_caller,
            cockpit_caller=cockpit_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
    except HTTPException as exc:
        return _attention_httpadvisor_book_error_response(exc, correlation_id)
    except (AdvisorBookCallerContextError, AdvisorBookServiceError) as exc:
        return advisor_book_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
        )


def _reject_non_advisor_advise_scope(
    cockpit_caller: AdvisorCockpitCallerContext,
    correlation_id: str,
) -> JSONResponse | None:
    authorize_advisor_cockpit_request(
        cockpit_caller,
        capability=ADVISOR_COCKPIT_READ_CAPABILITY,
        portfolio_id=None,
    )
    if cockpit_caller.authorized_portfolio_id is None:
        return None
    # A portfolio-scoped Advise entitlement cannot cover the whole book; zero counts
    # for the other members would be false claims, so fail closed.
    return advisor_book_error_response(
        status_code=403,
        code="advisor_book_attention_requires_advisor_scope",
        message=(
            "Book-wide attention requires an advisor-scoped Advise entitlement; a "
            "portfolio-scoped caller cannot state coverage for the whole book."
        ),
        correlation_id=correlation_id,
    )


def _attention_httpadvisor_book_error_response(
    exc: HTTPException, correlation_id: str
) -> JSONResponse:
    # Cockpit authorization and Advise source failures raise HTTPException; keep this
    # route's advertised AdvisorBookErrorResponse envelope for all of them.
    detail: dict[str, object] = exc.detail if isinstance(exc.detail, dict) else {}
    return advisor_book_error_response(
        status_code=exc.status_code,
        code=str(detail.get("code", "advisor_book_attention_source_unavailable")),
        message=str(
            detail.get(
                "message",
                "The Advise action feed is unavailable or could not be safely verified.",
            )
        ),
        correlation_id=correlation_id,
    )


@router.get(
    "/attention",
    response_model=AdvisorBookAttentionResponse,
    summary="Get advisor-book attention from Advise-owned actions",
    description=(
        "Returns per-portfolio attention counts for the authenticated advisor's active "
        "own-book membership cohort, composed from lotus-advise cockpit action items. Two "
        "independently admitted scopes meet here: Core owns the membership cohort and "
        "lotus-advise owns the action feed under the caller's Advise advisor scope; Gateway "
        "intersects them on portfolio identity only and never maps one caller identity onto "
        "the other. Counts are of source-owned actionable items with their own reason codes; "
        "Gateway does not reinterpret status, priority, or business meaning. Items outside "
        "the cohort or without a portfolio are reported as explicit counts, and a bounded "
        "page budget is surfaced as partial coverage rather than silent truncation."
    ),
    responses={
        200: {
            "description": "Attention facts for the authenticated advisor's own book.",
            "content": {"application/json": {"example": ADVISOR_BOOK_ATTENTION_RESPONSE_EXAMPLE}},
        },
        400: {
            "model": AdvisorBookErrorResponse,
            "description": "Required trusted advisor context is missing or invalid.",
        },
        401: {"description": "The Advise principal is not active."},
        403: {
            "model": AdvisorBookErrorResponse,
            "description": "The caller is not entitled to the book or Advise action scope.",
        },
        422: {"description": "A business-date input is invalid."},
        502: {
            "model": AdvisorBookErrorResponse,
            "description": "A source membership or action read is unavailable or unverified.",
        },
    },
)
async def get_advisor_book_attention(
    as_of_date: Annotated[date, Depends(advisor_book_attention_query)],
    caller_headers: Annotated[AdvisorBookCallerHeaders, Depends(advisor_book_caller_headers)],
    cockpit_caller: Annotated[AdvisorCockpitCallerContext, Depends(advisor_cockpit_caller_context)],
) -> AdvisorBookAttentionResponse | JSONResponse:
    return await _get_advisor_book_attention(
        as_of_date=as_of_date,
        caller_headers=caller_headers,
        cockpit_caller=cockpit_caller,
    )
