from app.contracts.reporting_batch_preflight import (
    ReportBatchPreflightResponse,
    ReportBatchPreflightSourcePosture,
)
from app.contracts.reporting_batches import BatchCreateRequest
from app.services.advisor_book_access_policy import AdvisorBookCallerContext
from app.services.advisor_book_service import AdvisorBookService
from app.services.advisor_book_service_errors import AdvisorBookServiceError
from app.services.advisor_book_source_contract import SourceAdvisorBookResponse
from app.services.reporting_batch_preflight_configuration import (
    load_report_configuration_posture,
)
from app.services.reporting_batch_preflight_projection import (
    build_response,
    configuration_posture,
    project_candidates,
    source_posture,
    source_posture_from_error,
    unavailable_response,
)
from app.services.reporting_batch_scope import (
    ReportingBatchScopeError,
    require_reporting_batch_caller,
)
from app.services.reporting_client_protocols import ReportingCatalogueClient


class ReportingBatchPreflightService:
    def __init__(
        self,
        *,
        membership_service: AdvisorBookService,
        reporting_client: ReportingCatalogueClient,
    ) -> None:
        self._membership_service = membership_service
        self._reporting_client = reporting_client

    async def preflight(
        self,
        *,
        request: BatchCreateRequest,
        caller_headers: dict[str, str],
        correlation_id: str,
    ) -> ReportBatchPreflightResponse:
        caller = require_reporting_batch_caller(caller_headers)
        source = await self._load_source(caller, request, correlation_id)
        if isinstance(source, ReportBatchPreflightResponse):
            return source
        if source is None:
            return unavailable_response(
                request=request,
                correlation_id=correlation_id,
                source_posture=ReportBatchPreflightSourcePosture(
                    state="unavailable",
                    reason_code="membership_source_unavailable",
                    message="Core returned no membership evidence for this caller.",
                ),
                reason_code="membership_source_unavailable",
                message="Portfolio reporting readiness is temporarily unavailable.",
            )
        source_result = self._source_posture(source)
        if source_result.state != "ready":
            return unavailable_response(
                request=request,
                correlation_id=correlation_id,
                source_posture=source_result,
                reason_code=source_result.reason_code,
                message="Portfolio reporting readiness cannot be safely verified.",
            )
        configuration = await load_report_configuration_posture(
            reporting_client=self._reporting_client,
            request=request,
            correlation_id=correlation_id,
        )
        return build_response(
            request=request,
            correlation_id=correlation_id,
            source_posture=source_result,
            configuration_posture=configuration_posture(configuration),
            candidates=project_candidates(
                request=request,
                source=source,
                configuration=configuration,
            ),
        )

    async def _load_source(
        self,
        caller: AdvisorBookCallerContext,
        request: BatchCreateRequest,
        correlation_id: str,
    ) -> SourceAdvisorBookResponse | ReportBatchPreflightResponse | None:
        try:
            return await self._membership_service.load_membership_source(
                caller=caller,
                as_of_date=request.as_of_date,
                correlation_id=correlation_id,
                include_inactive=True,
            )
        except AdvisorBookServiceError as exc:
            return self._source_error_response(exc, request, correlation_id)

    def _source_posture(
        self, source: SourceAdvisorBookResponse
    ) -> ReportBatchPreflightSourcePosture:
        posture = source_posture(source)
        if source.tenant_id is not None:
            return posture
        return ReportBatchPreflightSourcePosture(
            state="unavailable",
            reason_code="tenant_scope_unverified",
            message="Core did not confirm the tenant scope for membership evidence.",
            as_of_date=source.as_of_date,
        )

    def _source_error_response(
        self,
        exc: AdvisorBookServiceError,
        request: BatchCreateRequest,
        correlation_id: str,
    ) -> ReportBatchPreflightResponse:
        if exc.status_code == 403:
            raise ReportingBatchScopeError(
                code="report_batch_access_denied",
                message="Report batch preflight is not available for this caller.",
                status_code=403,
            ) from exc
        return unavailable_response(
            request=request,
            correlation_id=correlation_id,
            source_posture=source_posture_from_error(exc),
            reason_code="membership_source_unavailable",
            message="Portfolio reporting readiness is temporarily unavailable.",
        )
