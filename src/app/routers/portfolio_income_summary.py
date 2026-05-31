from fastapi import APIRouter, Query

from app.contracts.portfolio import PortfolioIncomeSummaryResponse
from app.middleware.correlation import correlation_id_var
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


async def _get_portfolio_income_summary(
    *,
    portfolio_id: str,
    as_of_date: str | None,
    start_date: str | None,
    end_date: str | None,
    reporting_currency: str | None,
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
    return await _get_portfolio_income_summary(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        start_date=start_date,
        end_date=end_date,
        reporting_currency=reporting_currency,
    )
