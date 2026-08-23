from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse, AdvisorBookResponse
from app.contracts.advisor_book_examples import ADVISOR_BOOK_RESPONSE_EXAMPLE
from app.contracts.advisor_book_summary import AdvisorBookSummaryResponse
from app.contracts.advisor_book_summary_examples import ADVISOR_BOOK_SUMMARY_RESPONSE_EXAMPLE
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_book_request import (
    AdvisorBookCallerHeaders,
    advisor_book_caller_headers,
    advisor_book_query,
    advisor_book_summary_query,
)
from app.services.advisor_book_access_policy import (
    AdvisorBookCallerContextError,
    require_advisor_book_caller_context,
)
from app.services.advisor_book_service import AdvisorBookQuery, AdvisorBookServiceError
from app.services.advisor_book_service_provider import advisor_book_service
from app.services.advisor_book_summary_service_provider import advisor_book_summary_service

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
        "attention, mandate, suitability, or recommendation truth."
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
