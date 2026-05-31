from fastapi import APIRouter, Query

from app.contracts.portfolio import (
    PortfolioActivitySummaryResponse,
    PortfolioIncomeSummaryResponse,
    PortfolioTransactionLedgerResponse,
)
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get(
    "/portfolios/{portfolio_id}/income-summary",
    response_model=PortfolioIncomeSummaryResponse,
    summary="Get portfolio income summary",
    description=(
        "Returns portfolio income totals for the requested reporting window and year-to-date. "
        "Use this endpoint for dividend and interest analysis when the UI needs "
        "reporting-currency-aware gross, tax, deduction, and net income totals by income type. "
        "Gateway derives these totals from the strategic lotus-core transaction ledger rather "
        "than the deprecated income-summary reporting route. The response keeps requested-window "
        "and year-to-date income cuts aligned to one reporting currency. When `end_date` is "
        "omitted, gateway uses `as_of_date` when provided or the current business date fallback."
    ),
)
async def get_portfolio_income_summary(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used as the default window end date when "
            "`end_date` is omitted."
        ),
        examples=["2026-03-27"],
    ),
    start_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window start date in YYYY-MM-DD format. When omitted, "
            "gateway uses the standard rolling 30-day window."
        ),
        examples=["2026-03-01"],
    ),
    end_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window end date in YYYY-MM-DD format. Defaults to "
            "`as_of_date` when provided."
        ),
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency used to restate portfolio income totals.",
        examples=["USD"],
    ),
) -> PortfolioIncomeSummaryResponse:
    return await portfolio_service().get_income_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/activity-summary",
    response_model=PortfolioActivitySummaryResponse,
    summary="Get portfolio activity summary",
    description=(
        "Returns portfolio flow buckets for the requested reporting window and year-to-date. "
        "Use this endpoint for inflow, outflow, fee, and tax analysis when the UI needs "
        "reporting-currency-aware activity totals aligned to the selected portfolio window. "
        "Gateway derives these buckets from the strategic lotus-core transaction ledger rather "
        "than the deprecated activity-summary reporting route. The response keeps requested-window "
        "and year-to-date bucket totals aligned to one reporting currency. When `end_date` is "
        "omitted, gateway uses `as_of_date` when provided or the current business date fallback."
    ),
)
async def get_portfolio_activity_summary(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description=(
            "Optional as-of date in YYYY-MM-DD format used as the default window end date when "
            "`end_date` is omitted."
        ),
        examples=["2026-03-27"],
    ),
    start_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window start date in YYYY-MM-DD format. When omitted, "
            "gateway uses the standard rolling 30-day window."
        ),
        examples=["2026-03-01"],
    ),
    end_date: str | None = Query(
        default=None,
        description=(
            "Optional inclusive reporting-window end date in YYYY-MM-DD format. Defaults to "
            "`as_of_date` when provided."
        ),
        examples=["2026-03-27"],
    ),
    reporting_currency: str | None = Query(
        default=None,
        description="Optional reporting currency used to restate portfolio activity totals.",
        examples=["USD"],
    ),
) -> PortfolioActivitySummaryResponse:
    return await portfolio_service().get_activity_summary(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )


@router.get(
    "/portfolios/{portfolio_id}/transactions",
    response_model=PortfolioTransactionLedgerResponse,
    summary="Get portfolio transaction ledger",
    description=(
        "Return the gateway transaction-ledger view for booked or projected portfolio activity. "
        "Use this endpoint for holdings drill-down, instrument-specific inspection, FX and "
        "linked-event analysis, and stable paging over the strategic lotus-core transaction "
        "ledger. The default ordering is latest-first by transaction date unless explicit "
        "sorting is requested."
    ),
)
async def get_portfolio_transactions(
    portfolio_id: str,
    as_of_date: str | None = Query(
        default=None,
        description="Optional as-of date in YYYY-MM-DD format used for booked transaction state.",
        examples=["2026-03-27"],
    ),
    include_projected: bool = Query(
        default=False,
        description="Whether future-dated projected transactions should be included.",
        examples=[False],
    ),
    transaction_type: str | None = Query(
        default=None,
        description="Optional canonical transaction type filter.",
        examples=["BUY"],
    ),
    security_id: str | None = Query(
        default=None,
        description="Optional security identifier filter for holdings drill-down.",
        examples=["EQ_1"],
    ),
    instrument_id: str | None = Query(
        default=None,
        description="Optional instrument identifier filter for instrument-specific inspection.",
        examples=["INST-AAPL-USD"],
    ),
    component_type: str | None = Query(
        default=None,
        description="Optional component-type filter for linked cash, trade, or FX event rows.",
        examples=["FX_CONTRACT_OPEN"],
    ),
    linked_transaction_group_id: str | None = Query(
        default=None,
        description="Optional linked-transaction-group filter for multi-row economic events.",
        examples=["LTG-FX-2026-0001"],
    ),
    fx_contract_id: str | None = Query(
        default=None,
        description="Optional FX contract identifier filter.",
        examples=["FXC-2026-0001"],
    ),
    swap_event_id: str | None = Query(
        default=None,
        description="Optional FX swap event identifier filter.",
        examples=["FXSWAP-2026-0001"],
    ),
    near_leg_group_id: str | None = Query(
        default=None,
        description="Optional FX swap near-leg group identifier filter.",
        examples=["FXSWAP-2026-0001-NEAR"],
    ),
    far_leg_group_id: str | None = Query(
        default=None,
        description="Optional FX swap far-leg group identifier filter.",
        examples=["FXSWAP-2026-0001-FAR"],
    ),
    start_date: str | None = Query(
        default=None,
        description="Optional inclusive transaction-window start date in YYYY-MM-DD format.",
        examples=["2026-03-01"],
    ),
    end_date: str | None = Query(
        default=None,
        description="Optional inclusive transaction-window end date in YYYY-MM-DD format.",
        examples=["2026-03-27"],
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of matching transaction rows to skip before returning the page.",
        examples=[0],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of matching transaction rows to return.",
        examples=[50],
    ),
    sort_by: str = Query(
        default="transaction_date",
        description="Transaction sort field. Defaults to transaction_date for latest-first review.",
        examples=["transaction_date"],
    ),
    sort_order: str = Query(
        default="desc",
        description="Transaction sort order. Use asc or desc.",
        examples=["desc"],
    ),
) -> PortfolioTransactionLedgerResponse:
    return await portfolio_service().get_transaction_ledger(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        transaction_type=transaction_type,
        security_id=security_id,
        instrument_id=instrument_id,
        component_type=component_type,
        linked_transaction_group_id=linked_transaction_group_id,
        fx_contract_id=fx_contract_id,
        swap_event_id=swap_event_id,
        near_leg_group_id=near_leg_group_id,
        far_leg_group_id=far_leg_group_id,
        sort_by=sort_by,
        sort_order=sort_order,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
