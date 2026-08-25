from typing import Any, Protocol, cast

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.portfolio_activity_income import (
    PortfolioActivitySummaryResponse,
    PortfolioIncomeSummaryResponse,
)
from app.contracts.portfolio_transactions import PortfolioTransactionLedgerResponse
from app.services.portfolio_transaction_activity_summary import build_activity_summary_response
from app.services.portfolio_transaction_ledger import (
    PortfolioTransactionLedgerRequest,
    PortfolioTransactionsRequestContext,
    build_transaction_ledger_response_for_request,
    build_transaction_rows_page_request_context,
)
from app.services.portfolio_transaction_summary import (
    InvalidPortfolioReportingWindow,
    PortfolioTransactionSummaryContext,
    PortfolioTransactionSummaryRequest,
    TransactionRowsPageRequest,
    build_income_summary_response,
    build_transaction_summary_context,
)
from app.services.portfolio_transaction_temporal import (
    PortfolioTransactionTemporalContractError,
)
from app.services.portfolio_upstream_payloads import require_payload

UpstreamResult = tuple[int, dict[str, Any]]


class _PortfolioTransactionUpstreamAccess(Protocol):
    async def _get_portfolio_transactions_result_for_context(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> UpstreamResult: ...


def _transaction_upstream_access(service: object) -> _PortfolioTransactionUpstreamAccess:
    return cast(_PortfolioTransactionUpstreamAccess, service)


class PortfolioTransactionServiceMixin:
    async def get_transaction_ledger(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        include_projected: bool,
        skip: int,
        limit: int,
        transaction_type: str | None = None,
        security_id: str | None = None,
        instrument_id: str | None = None,
        component_type: str | None = None,
        linked_transaction_group_id: str | None = None,
        fx_contract_id: str | None = None,
        swap_event_id: str | None = None,
        near_leg_group_id: str | None = None,
        far_leg_group_id: str | None = None,
        sort_by: str = "transaction_date",
        sort_order: str = "desc",
        start_date: str | None = None,
        end_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioTransactionLedgerResponse:
        request = PortfolioTransactionLedgerRequest(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            include_projected=include_projected,
            skip=skip,
            limit=limit,
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
            reporting_currency=reporting_currency,
        )
        return await self._build_transaction_ledger_response(request)

    async def _build_transaction_ledger_response(
        self,
        request: PortfolioTransactionLedgerRequest,
    ) -> PortfolioTransactionLedgerResponse:
        try:
            return await build_transaction_ledger_response_for_request(
                request=request,
                contract_version=settings.contract_version,
                load_payload=self._load_transaction_ledger_payload,
            )
        except PortfolioTransactionTemporalContractError as exc:
            raise _invalid_transaction_timestamp_contract() from exc

    async def _load_transaction_ledger_payload(
        self,
        context: PortfolioTransactionsRequestContext,
    ) -> dict[str, Any]:
        status_code, payload = await _transaction_upstream_access(
            self
        )._get_portfolio_transactions_result_for_context(context)
        return require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core transactions unavailable",
        )

    async def get_income_summary(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioIncomeSummaryResponse:
        context = await self._load_transaction_summary_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            reporting_currency=reporting_currency,
        )
        return build_income_summary_response(
            context=context,
            contract_version=settings.contract_version,
        )

    async def get_activity_summary(
        self,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        reporting_currency: str | None = None,
    ) -> PortfolioActivitySummaryResponse:
        context = await self._load_transaction_summary_context(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
            as_of_date=as_of_date,
            start_date=start_date,
            end_date=end_date,
            reporting_currency=reporting_currency,
        )
        return build_activity_summary_response(
            context=context,
            contract_version=settings.contract_version,
        )

    async def _load_transaction_summary_context(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        as_of_date: str | None,
        start_date: str | None,
        end_date: str | None,
        reporting_currency: str | None,
    ) -> PortfolioTransactionSummaryContext:
        try:
            return await build_transaction_summary_context(
                request=PortfolioTransactionSummaryRequest(
                    portfolio_id=portfolio_id,
                    correlation_id=correlation_id,
                    as_of_date=as_of_date,
                    start_date=start_date,
                    end_date=end_date,
                    reporting_currency=reporting_currency,
                ),
                page_loader=self._load_transaction_rows_page,
            )
        except InvalidPortfolioReportingWindow as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except PortfolioTransactionTemporalContractError as exc:
            raise _invalid_transaction_timestamp_contract() from exc

    async def _load_transaction_rows_page(
        self,
        request: TransactionRowsPageRequest,
    ) -> dict[str, Any]:
        context = build_transaction_rows_page_request_context(
            portfolio_id=request.portfolio_id,
            correlation_id=request.correlation_id,
            as_of_date=request.as_of_date,
            skip=request.skip,
            limit=request.limit,
            start_date=request.start_date,
            end_date=request.end_date,
            reporting_currency=request.reporting_currency,
        )
        status_code, payload = await _transaction_upstream_access(
            self
        )._get_portfolio_transactions_result_for_context(context)
        return require_payload(
            result=(status_code, payload),
            unavailable_detail_prefix="lotus-core transactions unavailable",
        )


def _invalid_transaction_timestamp_contract() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "code": "portfolio_transaction_source_contract_invalid",
            "message": (
                "lotus-core transaction ledger returned an invalid transaction timestamp contract"
            ),
        },
    )
