"""Advisor-book action-items route: Advise-owned action counts for the trusted book."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.contracts.advisor_book import AdvisorBookErrorResponse
from app.contracts.advisor_book_action_items import AdvisorBookActionItemsResponse
from app.contracts.advisor_book_action_items_examples import (
    ADVISOR_BOOK_ACTION_ITEMS_RESPONSE_EXAMPLE,
)
from app.middleware.correlation import correlation_id_var
from app.routers.advisor_book_request import (
    AdvisorBookCallerHeaders,
    advisor_book_attention_query,
    advisor_book_caller_headers,
    advisor_book_error_response,
    advisor_book_source_error_response,
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
from app.services.advisor_book_action_items_service_provider import (
    advisor_book_action_items_service,
)
from app.services.advisor_book_service_errors import AdvisorBookServiceError
from app.services.advisor_cockpit_access_policy import (
    ADVISOR_COCKPIT_READ_CAPABILITY,
    AdvisorCockpitAccessError,
    AdvisorCockpitCallerContext,
)

router = APIRouter(prefix="/api/v1/advisor-book", tags=["advisor-book"])

_SOURCE_UNAVAILABLE_MESSAGE = (
    "The Advise action feed is unavailable or could not be safely verified."
)


async def _get_advisor_book_action_items(
    *,
    as_of_date: date,
    caller_headers: AdvisorBookCallerHeaders,
    cockpit_headers: AdvisorCockpitCallerHeaders,
) -> AdvisorBookActionItemsResponse | JSONResponse:
    correlation_id = correlation_id_var.get()
    try:
        # Built inside the handler (not a dependency) so access failures are translated
        # into this route's advertised AdvisorBookErrorResponse envelope.
        cockpit_caller = build_advisor_cockpit_caller(cockpit_headers)
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
        return await advisor_book_action_items_service().get_action_items(
            book_caller=book_caller,
            cockpit_caller=cockpit_caller,
            as_of_date=as_of_date,
            correlation_id=correlation_id,
        )
    except HTTPException as exc:
        return advisor_book_source_error_response(
            exc,
            correlation_id=correlation_id,
            outage_code="advisor_book_action_items_source_unavailable",
            outage_message=_SOURCE_UNAVAILABLE_MESSAGE,
        )
    except (
        AdvisorCockpitAccessError,
        AdvisorBookCallerContextError,
        AdvisorBookServiceError,
    ) as exc:
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
    if (
        cockpit_caller.authorized_portfolio_id is None
        and cockpit_caller.authorized_advisor_id is not None
    ):
        return None
    # The advertised scope basis is one advisor's Advise feed. A portfolio-scoped
    # entitlement cannot cover the whole book, and an unscoped principal (for example
    # a supervisory role without X-Authorized-Advisor-Id) could receive a feed wider
    # than one advisor's book. Both fail closed before any source read.
    return advisor_book_error_response(
        status_code=403,
        code="advisor_book_action_items_requires_advisor_scope",
        message=(
            "Book-wide action items require exactly one advisor-scoped Advise "
            "entitlement; portfolio-scoped or unscoped callers cannot state coverage "
            "for the whole book."
        ),
        correlation_id=correlation_id,
    )


@router.get(
    "/action-items",
    response_model=AdvisorBookActionItemsResponse,
    summary="Get advisor-book action items",
    description=(
        "Returns per-portfolio counts of lotus-advise cockpit action items for the "
        "authenticated advisor's active own-book membership cohort. Two independently "
        "admitted scopes meet here: Core owns the membership cohort (resolved for the "
        "requested business date) and lotus-advise owns the action feed under the caller's "
        "advisor scope; Gateway intersects them on portfolio identity only and never maps "
        "one caller identity onto the other. Gateway counts the items the source returns — "
        "whatever their source status — with their own reason codes; actionable meaning "
        "stays with lotus-advise. Action items are current-state workflow evidence: a "
        "historical membership date never implies historical action evidence. The whole "
        "composition runs under one elapsed deadline; items outside the cohort or without "
        "a portfolio are explicit counts, and a stopped read is explicit partial coverage "
        "with every count a stated lower bound — never silent truncation or zero."
    ),
    responses={
        200: {
            "description": "Action-item facts for the authenticated advisor's own book.",
            "content": {
                "application/json": {"example": ADVISOR_BOOK_ACTION_ITEMS_RESPONSE_EXAMPLE}
            },
        },
        400: {
            "model": AdvisorBookErrorResponse,
            "description": "Required trusted caller context is missing or invalid.",
        },
        401: {
            "model": AdvisorBookErrorResponse,
            "description": "The Advise principal is not active.",
        },
        403: {
            "model": AdvisorBookErrorResponse,
            "description": "The caller is not entitled to the book or Advise action scope.",
        },
        422: {"description": "A business-date input is invalid."},
        502: {
            "model": AdvisorBookErrorResponse,
            "description": "A source membership or action read is unavailable or unverified.",
        },
        504: {
            "model": AdvisorBookErrorResponse,
            "description": "The composition deadline was exhausted before membership resolved.",
        },
    },
)
async def get_advisor_book_action_items(
    as_of_date: Annotated[date, Depends(advisor_book_attention_query)],
    caller_headers: Annotated[AdvisorBookCallerHeaders, Depends(advisor_book_caller_headers)],
    cockpit_headers: Annotated[
        AdvisorCockpitCallerHeaders, Depends(advisor_cockpit_caller_headers)
    ],
) -> AdvisorBookActionItemsResponse | JSONResponse:
    return await _get_advisor_book_action_items(
        as_of_date=as_of_date,
        caller_headers=caller_headers,
        cockpit_headers=cockpit_headers,
    )
