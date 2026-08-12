from datetime import date
from typing import Protocol

from app.contracts.reporting_batches import (
    BatchCreateRequest,
    PortfolioBatchCandidate,
    ReportBatchMaterializationRequest,
)
from app.services.advisor_book_access_policy import (
    AdvisorBookCallerContext,
    AdvisorBookCallerContextError,
    require_advisor_book_caller_context,
)
from app.services.advisor_book_service import (
    AdvisorBookServiceError,
    ResolvedAdvisorBookSelection,
)


class AdvisorBookPortfolioResolver(Protocol):
    async def resolve_portfolios(
        self,
        *,
        caller: AdvisorBookCallerContext,
        as_of_date: date,
        portfolio_ids: tuple[str, ...],
        correlation_id: str,
    ) -> ResolvedAdvisorBookSelection: ...


class ReportingBatchScopeError(RuntimeError):
    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ReportingBatchScopeResolver:
    def __init__(self, *, portfolio_resolver: AdvisorBookPortfolioResolver) -> None:
        self._portfolio_resolver = portfolio_resolver

    async def materialize_request(
        self,
        *,
        request: BatchCreateRequest,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportBatchMaterializationRequest:
        caller = _require_caller(caller_headers)
        try:
            selection = await self._portfolio_resolver.resolve_portfolios(
                caller=caller,
                as_of_date=request.as_of_date,
                portfolio_ids=tuple(request.portfolio_ids),
                correlation_id=correlation_id,
            )
        except AdvisorBookServiceError as exc:
            raise _map_selection_error(exc) from exc

        if selection.tenant_id != caller.tenant_id:
            raise ReportingBatchScopeError(
                code="report_batch_scope_unverified",
                message="The selected portfolio scope could not be safely verified.",
                status_code=502,
            )

        payload = request.model_dump(mode="json")
        payload["source_candidates"] = [
            PortfolioBatchCandidate(
                portfolio_id=portfolio.portfolio_id,
                tenant_id=selection.tenant_id,
                region=caller.region,
                active=True,
                selected=True,
                source_system="lotus-core",
                source_object=portfolio.membership_source,
            ).model_dump(mode="json")
            for portfolio in selection.portfolios
        ]
        return ReportBatchMaterializationRequest.model_validate(payload)


def _require_caller(caller_headers: dict[str, str]) -> AdvisorBookCallerContext:
    try:
        return require_advisor_book_caller_context(
            actor_id=caller_headers.get("X-Actor-Id"),
            caller_application=caller_headers.get("X-Caller-Application"),
            tenant_id=caller_headers.get("X-Tenant-Id"),
            region=caller_headers.get("X-Region"),
            booking_center_code=caller_headers.get("X-Booking-Center-Code"),
            role=caller_headers.get("X-Role"),
            capabilities=caller_headers.get("X-Caller-Capabilities"),
        )
    except AdvisorBookCallerContextError as exc:
        code = {
            "advisor_book_caller_context_missing": "report_batch_caller_context_missing",
            "advisor_book_caller_context_invalid": "report_batch_caller_context_invalid",
            "advisor_book_access_denied": "report_batch_access_denied",
        }.get(exc.code, "report_batch_access_denied")
        raise ReportingBatchScopeError(
            code=code,
            message=(
                "Required trusted report-batch caller context is missing or invalid."
                if exc.status_code == 400
                else "Report batch creation is not available for this caller."
            ),
            status_code=exc.status_code,
        ) from exc


def _map_selection_error(exc: AdvisorBookServiceError) -> ReportingBatchScopeError:
    mapped = {
        "advisor_book_portfolio_not_available": (
            "report_batch_portfolio_not_entitled",
            "One or more selected portfolios are not available in the authenticated book.",
            403,
        ),
        "advisor_book_portfolio_inactive": (
            "report_batch_portfolio_inactive",
            "One or more selected portfolios are not active for reporting.",
            409,
        ),
        "advisor_book_tenant_scope_unverified": (
            "report_batch_scope_unverified",
            "The selected portfolio scope could not be safely verified.",
            502,
        ),
        "advisor_book_tenant_scope_mismatch": (
            "report_batch_portfolio_not_entitled",
            "One or more selected portfolios are not available in the authenticated book.",
            403,
        ),
    }.get(
        exc.code,
        (
            "report_batch_scope_unavailable",
            "Report batch portfolio eligibility is temporarily unavailable.",
            502,
        ),
    )
    return ReportingBatchScopeError(code=mapped[0], message=mapped[1], status_code=mapped[2])
