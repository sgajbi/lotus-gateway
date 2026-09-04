"""Exact portfolio transaction record lookup (issue #570)."""

from fastapi import APIRouter, Path, Query, status

from app.contracts.portfolio_transactions import PortfolioTransactionRecordResponse
from app.middleware.correlation import correlation_id_var
from app.routers.portfolio_transactions import AS_OF_DATE_QUERY, INCLUDE_PROJECTED_QUERY
from app.services.portfolio_service_provider import portfolio_service

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])

REPORTING_CURRENCY_QUERY = Query(
    default=None,
    description=(
        "Optional reporting currency for source-owned monetary restatement of the exact record."
    ),
    examples=["SGD"],
)


@router.get(
    "/portfolios/{portfolio_id}/transactions/{transaction_id}",
    response_model=PortfolioTransactionRecordResponse,
    summary="Get exact portfolio transaction record",
    description=(
        "Return exactly one source-owned transaction record by portfolio and transaction "
        "identity, for URL rehydration and record drill-down. The lookup is a single bounded "
        "lotus-core read: it never scans the paginated ledger, and a transaction owned by "
        "another portfolio is indistinguishable from an absent transaction. Business fields, "
        "currency and date semantics match the transaction ledger."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "lotus-core rejected the exact record query as invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "lotus-core denied access to the requested portfolio transaction.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": (
                "No transaction with this identifier is visible within the requested portfolio."
            ),
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": (
                "lotus-core is unavailable or returned a record that does not match the "
                "requested identity."
            ),
        },
    },
)
async def get_portfolio_transaction_record(
    portfolio_id: str = Path(
        description="Portfolio boundary that must own the transaction.",
        min_length=1,
    ),
    transaction_id: str = Path(
        description="Exact source-owned transaction identifier.",
        min_length=1,
    ),
    as_of_date: str | None = AS_OF_DATE_QUERY,
    include_projected: bool = INCLUDE_PROJECTED_QUERY,
    reporting_currency: str | None = REPORTING_CURRENCY_QUERY,
) -> PortfolioTransactionRecordResponse:
    return await _get_portfolio_transaction_record(
        portfolio_id=portfolio_id,
        transaction_id=transaction_id,
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )


async def _get_portfolio_transaction_record(
    *,
    portfolio_id: str,
    transaction_id: str,
    as_of_date: str | None,
    include_projected: bool,
    reporting_currency: str | None,
) -> PortfolioTransactionRecordResponse:
    return await portfolio_service().get_transaction_record(
        portfolio_id=portfolio_id,
        transaction_id=transaction_id,
        correlation_id=correlation_id_var.get(),
        as_of_date=as_of_date,
        include_projected=include_projected,
        reporting_currency=reporting_currency,
    )
