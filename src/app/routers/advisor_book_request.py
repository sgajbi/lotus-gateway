from dataclasses import dataclass
from datetime import date
from typing import Annotated, Literal

from fastapi import Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse
from app.services.advisor_book_service import AdvisorBookQuery

_AsOfDate = Annotated[
    date,
    Query(
        alias="asOfDate",
        description="Business date used to resolve effective advisor-book membership.",
        examples=["2026-04-10"],
    ),
]
_ClientId = Annotated[
    str | None,
    Query(
        alias="clientId",
        min_length=1,
        max_length=128,
        description="Optional exact client identifier within the authenticated book.",
    ),
]
_MandateType = Annotated[
    Literal["ADVISORY", "DISCRETIONARY"] | None,
    Query(
        alias="mandateType",
        description="Optional supported mandate type within the authenticated book.",
    ),
]
_SortBy = Annotated[
    Literal["portfolio_id", "client_id", "mandate_type"],
    Query(alias="sortBy", description="Business field used for deterministic ordering."),
]
_SortOrder = Annotated[
    Literal["asc", "desc"],
    Query(alias="sortOrder", description="Deterministic result ordering direction."),
]
_Offset = Annotated[
    int,
    Query(ge=0, description="Zero-based result offset within the authenticated book."),
]
_Limit = Annotated[
    int,
    Query(ge=1, le=100, description="Maximum number of portfolios returned on this page."),
]
_ReportingCurrency = Annotated[
    str,
    Query(
        alias="reportingCurrency",
        min_length=3,
        max_length=3,
        description="Explicit reporting currency required for a cross-portfolio book value total.",
        examples=["USD"],
    ),
]


@dataclass(frozen=True)
class AdvisorBookCallerHeaders:
    actor_id: str | None
    caller_application: str | None
    tenant_id: str | None
    region: str | None
    booking_center_code: str | None
    role: str | None
    capabilities: str | None


def advisor_book_caller_headers(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
    capabilities: Annotated[str | None, Header(alias="X-Caller-Capabilities")] = None,
) -> AdvisorBookCallerHeaders:
    return AdvisorBookCallerHeaders(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
        capabilities=capabilities,
    )


def advisor_book_query(
    as_of_date: _AsOfDate,
    client_id: _ClientId = None,
    mandate_type: _MandateType = None,
    sort_by: _SortBy = "portfolio_id",
    sort_order: _SortOrder = "asc",
    offset: _Offset = 0,
    limit: _Limit = 25,
) -> AdvisorBookQuery:
    return AdvisorBookQuery(
        as_of_date=as_of_date,
        client_id=_optional_filter(client_id),
        mandate_type=mandate_type,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )


def advisor_book_summary_query(
    as_of_date: _AsOfDate,
    reporting_currency: _ReportingCurrency,
) -> tuple[date, str]:
    normalized_currency = reporting_currency.strip().upper()
    if not normalized_currency.isalpha():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "advisor_book_reporting_currency_invalid",
                "message": "Reporting currency must be a three-letter alphabetic code.",
            },
        )
    return as_of_date, normalized_currency


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


def advisor_book_attention_query(as_of_date: _AsOfDate) -> date:
    return as_of_date


def advisor_book_error_response(
    *, status_code: int, code: str, message: str, correlation_id: str
) -> JSONResponse:
    error = AdvisorBookErrorResponse(
        code=code,
        message=message,
        correlation_id=correlation_id,
    )
    return JSONResponse(status_code=status_code, content=error.model_dump(mode="json"))
