from pydantic import ValidationError

from app.contracts.report_ordering import (
    ReportScopeSelection,
    ReportSectionAcceptedBrief,
    ReportSectionAvailability,
    WorkbenchReportOrderingResponse,
)
from app.contracts.report_ordering_source import (
    SourceAdvisorCommentaryAvailability,
    SourceReportOrderingCatalogue,
)
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
        as_of_date: str | None = None,
        reporting_currency: str | None = None,
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
            advisor_commentary_availability=await self._advisor_commentary_availability(
                selection=selection,
                caller_headers=caller_headers,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            ),
        )

    async def _advisor_commentary_availability(
        self,
        *,
        selection: ReportScopeSelection | None,
        caller_headers: dict[str, str],
        correlation_id: str,
        as_of_date: str | None,
        reporting_currency: str | None,
    ) -> ReportSectionAvailability | None:
        """Scope-specific ADVISOR_COMMENTARY availability (issue #688, rescoped).

        Evaluated only for a single-portfolio scope with a tenant-bound caller -
        the one case where "does an accepted brief exist?" has a well-defined
        answer. Everything Reporting cannot prove maps to
        ``advisor_brief_availability_unknown``; the reason vocabulary passes
        through untranslated, and a failed lookup never becomes
        ``advisor_brief_not_reviewed`` because it proves nothing.
        """

        if selection is None or selection.scope_type != "portfolio":
            return None
        tenant_id = caller_headers.get("X-Tenant-Id", "").strip()
        if not tenant_id:
            return None
        try:
            status_code, payload = await self._reporting_client.get_advisor_commentary_availability(
                portfolio_id=selection.scope_id,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                as_of_date=as_of_date,
                reporting_currency=reporting_currency,
            )
        except Exception:
            return _section_availability_unknown(
                "The section-availability lookup could not be reached."
            )
        return _map_availability_response(status_code, payload)


def _map_availability_response(status_code: int, payload: dict) -> ReportSectionAvailability:
    if status_code != 200:
        return _section_availability_unknown(
            "The section-availability lookup could not answer for this portfolio."
        )
    try:
        source = SourceAdvisorCommentaryAvailability.model_validate(payload)
    except ValidationError:
        return _section_availability_unknown(
            "The section-availability lookup answered with an unrecognised contract."
        )
    return ReportSectionAvailability(
        state=source.state,
        reasonCode=source.reason_code,
        message=source.message,
        acceptedBrief=(
            ReportSectionAcceptedBrief(
                runId=source.accepted_brief.run_id,
                reviewedBy=source.accepted_brief.reviewed_by,
                reviewedAt=source.accepted_brief.reviewed_at,
            )
            if source.accepted_brief is not None
            else None
        ),
    )


def _section_availability_unknown(message: str) -> ReportSectionAvailability:
    return ReportSectionAvailability(
        state="unavailable",
        reasonCode="advisor_brief_availability_unknown",
        message=(
            f"{message} This does not mean no accepted brief exists; retry or order "
            "without the section."
        ),
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
