from app.config import settings
from app.services.domain_product_catalog_service import DomainProductCatalogService


def build_domain_product_catalog_service() -> DomainProductCatalogService:
    return DomainProductCatalogService(
        catalog_path=settings.domain_product_catalog_path,
        dependency_graph_path=settings.domain_product_dependency_graph_path,
        live_trust_certification_path=settings.domain_product_live_trust_certification_path,
    )
