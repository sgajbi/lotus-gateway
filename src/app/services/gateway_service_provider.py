from app.services.archive_document_service import ArchiveDocumentService
from app.services.archive_document_service_factory import (
    archive_document_service_signature,
    build_archive_document_service,
)
from app.services.composite_performance_service import CompositePerformanceService
from app.services.composite_performance_service_factory import (
    build_composite_performance_service,
    composite_performance_service_signature,
)
from app.services.domain_product_catalog_service import DomainProductCatalogService
from app.services.domain_product_catalog_service_factory import (
    build_domain_product_catalog_service,
    domain_product_catalog_service_signature,
)
from app.services.foundation_service import FoundationService
from app.services.foundation_service_factory import (
    build_foundation_service,
    foundation_service_signature,
)
from app.services.intake_service import IntakeService
from app.services.intake_service_factory import build_intake_service, intake_service_signature
from app.services.service_provider_cache import resolve_cached_service
from app.services.source_product_execution_service import SourceProductExecutionService
from app.services.source_product_execution_service_factory import (
    build_source_product_execution_service,
    source_product_execution_service_signature,
)

_ARCHIVE_DOCUMENT_SERVICE: ArchiveDocumentService | None = None
_ARCHIVE_DOCUMENT_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_DOMAIN_PRODUCT_CATALOG_SERVICE: DomainProductCatalogService | None = None
_DOMAIN_PRODUCT_CATALOG_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_COMPOSITE_PERFORMANCE_SERVICE: CompositePerformanceService | None = None
_COMPOSITE_PERFORMANCE_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_SOURCE_PRODUCT_SERVICE: SourceProductExecutionService | None = None
_SOURCE_PRODUCT_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_FOUNDATION_SERVICE: FoundationService | None = None
_FOUNDATION_SERVICE_SIGNATURE: tuple[object, ...] | None = None
_INTAKE_SERVICE: IntakeService | None = None
_INTAKE_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def archive_document_service() -> ArchiveDocumentService:
    global _ARCHIVE_DOCUMENT_SERVICE, _ARCHIVE_DOCUMENT_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _ARCHIVE_DOCUMENT_SERVICE,
        _ARCHIVE_DOCUMENT_SERVICE_SIGNATURE,
        archive_document_service_signature(),
        build_archive_document_service,
    )
    _ARCHIVE_DOCUMENT_SERVICE = service
    _ARCHIVE_DOCUMENT_SERVICE_SIGNATURE = signature
    return service


def domain_product_catalog_service() -> DomainProductCatalogService:
    global _DOMAIN_PRODUCT_CATALOG_SERVICE, _DOMAIN_PRODUCT_CATALOG_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _DOMAIN_PRODUCT_CATALOG_SERVICE,
        _DOMAIN_PRODUCT_CATALOG_SERVICE_SIGNATURE,
        domain_product_catalog_service_signature(),
        build_domain_product_catalog_service,
    )
    _DOMAIN_PRODUCT_CATALOG_SERVICE = service
    _DOMAIN_PRODUCT_CATALOG_SERVICE_SIGNATURE = signature
    return service


def composite_performance_service() -> CompositePerformanceService:
    global _COMPOSITE_PERFORMANCE_SERVICE, _COMPOSITE_PERFORMANCE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _COMPOSITE_PERFORMANCE_SERVICE,
        _COMPOSITE_PERFORMANCE_SERVICE_SIGNATURE,
        composite_performance_service_signature(),
        build_composite_performance_service,
    )
    _COMPOSITE_PERFORMANCE_SERVICE = service
    _COMPOSITE_PERFORMANCE_SERVICE_SIGNATURE = signature
    return service


def source_product_service() -> SourceProductExecutionService:
    global _SOURCE_PRODUCT_SERVICE, _SOURCE_PRODUCT_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _SOURCE_PRODUCT_SERVICE,
        _SOURCE_PRODUCT_SERVICE_SIGNATURE,
        source_product_execution_service_signature(),
        build_source_product_execution_service,
    )
    _SOURCE_PRODUCT_SERVICE = service
    _SOURCE_PRODUCT_SERVICE_SIGNATURE = signature
    return service


def foundation_service() -> FoundationService:
    global _FOUNDATION_SERVICE, _FOUNDATION_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _FOUNDATION_SERVICE,
        _FOUNDATION_SERVICE_SIGNATURE,
        foundation_service_signature(),
        build_foundation_service,
    )
    _FOUNDATION_SERVICE = service
    _FOUNDATION_SERVICE_SIGNATURE = signature
    return service


def intake_service() -> IntakeService:
    global _INTAKE_SERVICE, _INTAKE_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _INTAKE_SERVICE,
        _INTAKE_SERVICE_SIGNATURE,
        intake_service_signature(),
        build_intake_service,
    )
    _INTAKE_SERVICE = service
    _INTAKE_SERVICE_SIGNATURE = signature
    return service
