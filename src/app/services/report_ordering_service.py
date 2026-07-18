from pydantic import ValidationError

from app.contracts.report_ordering import (
    ReportScopeSelection,
    WorkbenchReportOrderingResponse,
)
from app.contracts.report_ordering_source import SourceReportOrderingCatalogue
from app.services.report_ordering_eligibility import ReportOrderingEntitlements
from app.services.report_ordering_projection import (
    project_report_ordering_catalogue,
    unavailable_report_ordering_response,
)
from app.services.reporting_client_protocols import ReportingCatalogueClient


class ReportOrderingService:
    def __init__(self, *, reporting_client: ReportingCatalogueClient) -> None:
        self._reporting_client = reporting_client

    async def get_ordering_options(
        self,
        *,
        selection: ReportScopeSelection | None,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> WorkbenchReportOrderingResponse:
        entitlements = ReportOrderingEntitlements.from_headers(caller_headers)
        try:
            status_code, payload = await self._reporting_client.get_report_ordering_catalogue(
                correlation_id=correlation_id,
            )
        except Exception:
            return _unavailable(
                selection,
                entitlements,
                reason_code="report_catalogue_unavailable",
            )
        if status_code >= 400:
            return _unavailable(
                selection,
                entitlements,
                reason_code="report_catalogue_unavailable",
            )
        try:
            source = SourceReportOrderingCatalogue.model_validate(payload)
        except ValidationError:
            return _unavailable(
                selection,
                entitlements,
                reason_code="report_catalogue_contract_invalid",
            )
        return project_report_ordering_catalogue(
            source=source,
            selection=selection,
            entitlements=entitlements,
        )


def _unavailable(
    selection: ReportScopeSelection | None,
    entitlements: ReportOrderingEntitlements,
    *,
    reason_code: str,
) -> WorkbenchReportOrderingResponse:
    return unavailable_report_ordering_response(
        selection=selection,
        entitlements=entitlements,
        reason_code=reason_code,
        message="Report choices are temporarily unavailable.",
    )
