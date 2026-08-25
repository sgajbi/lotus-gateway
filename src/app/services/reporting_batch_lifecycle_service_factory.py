from app.services.advisor_book_service_factory import (
    advisor_book_service_signature,
    build_advisor_book_service,
)
from app.services.archive_client_factory import archive_client_signature, build_archive_client
from app.services.reporting_batch_lifecycle_service import ReportingBatchLifecycleService
from app.services.reporting_batch_scope import ReportingBatchScopeResolver
from app.services.reporting_client_factory import (
    build_render_client,
    build_reporting_client,
    render_client_signature,
    reporting_client_signature,
)


def reporting_batch_lifecycle_service_signature() -> tuple[object, ...]:
    return (
        *reporting_client_signature(),
        *archive_client_signature(),
        *render_client_signature(),
        *advisor_book_service_signature(),
    )


def build_reporting_batch_lifecycle_service() -> ReportingBatchLifecycleService:
    return ReportingBatchLifecycleService(
        reporting_client=build_reporting_client(),
        archive_access_client=build_archive_client(),
        render_client=build_render_client(),
        scope_resolver=ReportingBatchScopeResolver(portfolio_resolver=build_advisor_book_service()),
    )
