from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse, AdvisorBookResponse
from app.contracts.advisor_book_examples import ADVISOR_BOOK_RESPONSE_EXAMPLE
from app.middleware.correlation import correlation_id_var
from app.services.advisor_book_access_policy import (
    AdvisorBookCallerContextError,
    require_advisor_book_caller_context,
)
from app.services.advisor_book_service import AdvisorBookQuery, AdvisorBookServiceError
from app.services.advisor_book_service_provider import advisor_book_service

router = APIRouter(prefix="/api/v1/advisor-book", tags=["advisor-book"])


async def _get_advisor_book(
    *,
    as_of_date: date,
    client_id: str | None,
    mandate_type: Literal["ADVISORY", "DISCRETIONARY"] | None,
    sort_by: Literal["portfolio_id", "client_id", "mandate_type"],
    sort_order: Literal["asc", "desc"],
    offset: int,
    limit: int,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
    capabilities: str | None,
) -> AdvisorBookResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        caller = require_advisor_book_caller_context(
            actor_id=actor_id,
            caller_application=caller_application,
            tenant_id=tenant_id,
            region=region,
            booking_center_code=booking_center_code,
            role=role,
            capabilities=capabilities,
        )
        return await advisor_book_service().get_advisor_book(
            caller=caller,
            query=AdvisorBookQuery(
                as_of_date=as_of_date,
                client_id=_optional_filter(client_id),
                mandate_type=mandate_type,
                sort_by=sort_by,
                sort_order=sort_order,
                offset=offset,
                limit=limit,
            ),
            correlation_id=correlation_id,
        )
    except (AdvisorBookCallerContextError, AdvisorBookServiceError) as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
        )


def _optional_filter(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "advisor_book_filter_invalid",
                "message": "Advisor-book filters must contain a business identifier.",
            },
        )
    return cleaned


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
    as_of_date: Annotated[
        date,
        Query(
            alias="asOfDate",
            description="Business date used to resolve effective advisor-book membership.",
            examples=["2026-04-10"],
        ),
    ],
    client_id: Annotated[
        str | None,
        Query(
            alias="clientId",
            min_length=1,
            max_length=128,
            description="Optional exact client identifier within the authenticated book.",
        ),
    ] = None,
    mandate_type: Annotated[
        Literal["ADVISORY", "DISCRETIONARY"] | None,
        Query(
            alias="mandateType",
            description="Optional supported mandate type within the authenticated book.",
        ),
    ] = None,
    sort_by: Annotated[
        Literal["portfolio_id", "client_id", "mandate_type"],
        Query(alias="sortBy", description="Business field used for deterministic ordering."),
    ] = "portfolio_id",
    sort_order: Annotated[
        Literal["asc", "desc"],
        Query(alias="sortOrder", description="Deterministic result ordering direction."),
    ] = "asc",
    offset: Annotated[
        int,
        Query(ge=0, description="Zero-based result offset within the authenticated book."),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of portfolios returned on this page."),
    ] = 25,
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
) -> AdvisorBookResponse | JSONResponse:
    return await _get_advisor_book(
        as_of_date=as_of_date,
        client_id=client_id,
        mandate_type=mandate_type,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
        capabilities=capabilities,
    )
