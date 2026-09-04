from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse, AdvisorBookResponse
from app.contracts.advisor_book_attention import AdvisorBookAttentionResponse
from app.contracts.advisor_book_attention_examples import ADVISOR_BOOK_ATTENTION_RESPONSE_EXAMPLE
from app.contracts.advisor_book_examples import ADVISOR_BOOK_RESPONSE_EXAMPLE
from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse
from app.contracts.advisor_book_summary_examples import ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_book_request import (
    AdvisorBookCallerHeaders,
    advisor_book_attention_query,
    advisor_book_caller_headers,
    advisor_book_query,
    advisor_book_summary_query,
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
from app.services.advisor_book_service import AdvisorBookQuery, AdvisorBookServiceError
from app.services.advisor_book_service_provider import advisor_book_service
from app.services.advisor_book_summary_service_provider import advisor_book_summary_service
from app.services.advisor_cockpit_access_policy import (
    ADVISOR_COCKPIT_READ_CAPABILITY,
    AdvisorCockpitCallerContext,
)

router = APIRouter(prefix="/api/v1/advisor-book", tags=["advisor-book"])


async def _get_advisor_book(
    *,
    query: AdvisorBookQuery,
    caller_headers: AdvisorBookCallerHeaders,
) -> AdvisorBookResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = require_advisor_book_caller_context(
            actor_id=caller_headers.actor_id,
            caller_application=caller_headers.caller_application,
            tenant_id=caller_headers.tenant_id,
            region=caller_headers.region,
            booking_center_code=caller_headers.booking_center_code,
            role=caller_headers.role,
            capabilities=caller_headers.capabilities,
        )
        return await advisor_book_service().get_advisor_book(
            caller=caller,
            query=query,
            correlation_id=correlation_id,
        )
    except (AdvisorBookCallerContextError, AdvisorBookServiceError) as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
        )


async def _get_advisor_book_summary(
    *,
    query: tuple[date, str],
    caller_headers: AdvisorBookCallerHeaders,
) -> AdvisorBookSummaryResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = require_advisor_book_caller_context(
            actor_id=caller_headers.actor_id,
            caller_application=caller_headers.caller_application,
            tenant_id=caller_headers.tenant_id,
            region=caller_headers.region,
            booking_center_code=caller_headers.booking_center_code,
            role=caller_headers.role,
            capabilities=caller_headers.capabilities,
        )
        as_of_date, reporting_currency = query
        return await advisor_book_summary_service().get_value_summary(
            caller=caller,
            as_of_date=as_of_date,
            reporting_currency=reporting_currency,
            correlation_id=correlation_id,
        )
    except (AdvisorBookCallerContextError, AdvisorBookServiceError) as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
        )


def _error_response(
    *, status_code: int, code: str, message: str, correlation_id: str
) -> JSONResponse:
    error = AdvisorBookErrorResponse(
        code=code,
        message=message,
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status_code, content=error.model_dump(mode="json"))


@router.get(
    "/portfolios",
    response_model=AdvisorBookResponse,
    summary="Get my advisor book",
    description=(
        "Returns the authenticated advisor's source-backed portfolio book for the requested "
        "business date and trusted booking centre. The scope is derived only from trusted caller "
        "context; callers cannot request another advisor's book. Results may be filtered, sorted, "
        "and paged without widening the Core membership cohort. The response explicitly reports "
        "tenant-scope and legacy-membership limitations and does not claim delegated, team, "
        "household, assets-under-management, or attention-indicator coverage."
    ),
    responses={
        200: {
            "description": "Source-backed portfolios in the authenticated advisor's own book.",
            "content": {"application/json": {"example": ADVISOR_BOOK_RESPONSE_EXAMPLE}},
        },
        400: {
            "model": AdvisorBookErrorResponse,
            "description": "Required trusted advisor context is missing or invalid.",
        },
        403: {
            "model": AdvisorBookErrorResponse,
            "description": "The caller is not entitled to the requested own-book experience.",
        },
        422: {"description": "A business-date, filter, sort, or paging input is invalid."},
        502: {
            "model": AdvisorBookErrorResponse,
            "description": "The source book is unavailable or could not be safely verified.",
        },
    },
)
async def get_advisor_book(
    query: Annotated[AdvisorBookQuery, Depends(advisor_book_query)],
    caller_headers: Annotated[AdvisorBookCallerHeaders, Depends(advisor_book_caller_headers)],
) -> AdvisorBookResponse | JSONResponse:
    return await _get_advisor_book(
        query=query,
        caller_headers=caller_headers,
    )


@router.get(
    "/summary",
    response_model=AdvisorBookSummaryResponse,
    summary="Get source-backed advisor-book value summary",
    description=(
        "Returns Core-owned total value facts for the authenticated advisor's active own-book "
        "membership cohort. The caller must provide an explicit business date and reporting "
        "currency because a book may contain portfolios with different base currencies. Gateway "
        "resolves membership from trusted caller context and performs one bounded Core AUM scope "
        "read; it does not value holdings, sum partial rows, or claim performance, cash, risk, "
        "attention, mandate, suitability, or recommendation truth. Core's current AUM contract "
        "does not expose per-portfolio snapshot freshness, so the response does not certify every "
        "value fact as current on the requested date."
    ),
    responses={
        200: {
            "description": "Source-backed value facts for the authenticated advisor's own book.",
            "content": {"application/json": {"example": ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE}},
        },
        400: {
            "model": AdvisorBookErrorResponse,
            "description": "Required trusted advisor context is missing or invalid.",
        },
        403: {
            "model": AdvisorBookErrorResponse,
            "description": "The caller is not entitled to the requested own-book experience.",
        },
        422: {"description": "A business-date or reporting-currency input is invalid."},
        502: {
            "model": AdvisorBookErrorResponse,
            "description": "The source book or value read is unavailable or could not be verified.",
        },
    },
)
async def get_advisor_book_summary(
    query: Annotated[tuple[date, str], Depends(advisor_book_summary_query)],
    caller_headers: Annotated[AdvisorBookCallerHeaders, Depends(advisor_book_caller_headers)],
) -> AdvisorBookSummaryResponse | JSONResponse:
    return await _get_advisor_book_summary(
        query=query,
        caller_headers=caller_headers,
    )


async def _get_advisor_book_attention(
    *,
    as_of_date: date,
    caller_headers: AdvisorBookCallerHeaders,
    cockpit_caller: AdvisorCockpitCallerContext,
) -> AdvisorBookAttentionResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    authorize_advisor_cockpit_request(
        cockpit_caller,
        capability=ADVISOR_COCKPIT_READ_CAPABILITY,
        portfolio_id=None,
    )
    if cockpit_caller.authorized_portfolio_id is not None:
        # A portfolio-scoped Advise entitlement cannot cover the whole book; zero
        # counts for the other members would be false claims, so fail closed.
        return _error_response(
            status_code=403,
            code="advisor_book_attention_requires_advisor_scope",
            message=(
                "Book-wide attention requires an advisor-scoped Advise entitlement; a "
                "portfolio-scoped caller cannot state coverage for the whole book."
            ),
            correlation_id=correlation_id,
        )
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
        return await advisor_book_attention_service().get_attention(
            book_caller=book_caller,
            cockpit_caller=cockpit_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
    except (AdvisorBookCallerContextError, AdvisorBookServiceError) as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
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
