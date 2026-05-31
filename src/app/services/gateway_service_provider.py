from app.services.archive_document_service import ArchiveDocumentService
from app.services.archive_document_service_factory import build_archive_document_service
from app.services.composite_performance_service import CompositePerformanceService
from app.services.composite_performance_service_factory import (
    build_composite_performance_service,
)
from app.services.domain_product_catalog_service import DomainProductCatalogService
from app.services.domain_product_catalog_service_factory import (
    build_domain_product_catalog_service,
)
from app.services.foundation_service import FoundationService
from app.services.foundation_service_factory import build_foundation_service
from app.services.intake_service import IntakeService
from app.services.intake_service_factory import build_intake_service
from app.services.source_product_execution_service import SourceProductExecutionService
from app.services.source_product_execution_service_factory import (
    build_source_product_execution_service,
)


def archive_document_service() -> ArchiveDocumentService:
    return build_archive_document_service()


def domain_product_catalog_service() -> DomainProductCatalogService:
    return build_domain_product_catalog_service()


def composite_performance_service() -> CompositePerformanceService:
    return build_composite_performance_service()


def source_product_service() -> SourceProductExecutionService:
    return build_source_product_execution_service()


def foundation_service() -> FoundationService:
    return build_foundation_service()


def intake_service() -> IntakeService:
    return build_intake_service()
