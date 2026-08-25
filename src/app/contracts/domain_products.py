from typing import Any

from pydantic import BaseModel, Field

from app.contracts.domain_product_failure_posture import (
    DomainProductFailurePostureCondition,
)
from app.contracts.domain_product_graph import (
    DomainProductGraphData as DomainProductGraphData,
)
from app.contracts.domain_product_graph import (
    DomainProductGraphEdge as DomainProductGraphEdge,
)
from app.contracts.domain_product_graph import (
    DomainProductGraphNode as DomainProductGraphNode,
)
from app.contracts.domain_product_graph import (
    DomainProductGraphResponse as DomainProductGraphResponse,
)
from app.contracts.domain_product_trust import (
    DomainProductLiveTrustCertification as DomainProductLiveTrustCertification,
)
from app.contracts.domain_product_trust import (
    DomainProductLiveTrustIssue as DomainProductLiveTrustIssue,
)
from app.contracts.domain_product_trust import (
    DomainProductLiveTrustSummary as DomainProductLiveTrustSummary,
)
from app.contracts.domain_product_trust import (
    DomainProductTrustCertificationData as DomainProductTrustCertificationData,
)
from app.contracts.domain_product_trust import (
    DomainProductTrustCertificationResponse as DomainProductTrustCertificationResponse,
)


class DomainProductRepositorySummary(BaseModel):
    repository: str = Field(description="Lotus repository that produces or consumes products.")
    produced_product_count: int = Field(
        alias="producedProductCount",
        description="Number of domain products declared by the repository.",
    )
    consumed_dependency_count: int = Field(
        alias="consumedDependencyCount",
        description="Number of governed domain-product dependencies declared by the repository.",
    )

    model_config = {"populate_by_name": True}


class DomainProduct(BaseModel):
    product_id: str = Field(
        alias="productId",
        description="Stable governed domain-product identity.",
        examples=["lotus-core:PortfolioStateSnapshot:v1"],
    )
    product_name: str = Field(alias="productName", description="Domain-product name.")
    product_version: str = Field(alias="productVersion", description="Domain-product version.")
    producer_repository: str = Field(
        alias="producerRepository",
        description="Repository that produces and owns the product contract.",
    )
    owner_repository: str = Field(
        alias="ownerRepository",
        description="Authoritative repository responsible for product correctness.",
    )
    authoritative_domain: str = Field(
        alias="authoritativeDomain",
        description="Business domain for which the product is authoritative.",
    )
    product_family: str = Field(
        alias="productFamily",
        description="Governed product-family classification.",
    )
    lifecycle_status: str = Field(
        alias="lifecycleStatus",
        description="Current product lifecycle state.",
    )
    request_scope: dict[str, Any] = Field(
        alias="requestScope",
        description="Declared request-scope metadata from the platform catalog.",
    )
    temporal_scope: dict[str, Any] = Field(
        alias="temporalScope",
        description="Declared temporal semantics for freshness and restatement behavior.",
    )
    temporal_semantics_ref: str = Field(
        alias="temporalSemanticsRef",
        description="Reference into the governed temporal-semantics registry.",
    )
    identifier_refs: list[str] = Field(
        alias="identifierRefs",
        description="Governed identifier references required by this product.",
    )
    required_trust_metadata: list[str] = Field(
        alias="requiredTrustMetadata",
        description="Trust metadata fields required on product payloads or evidence.",
    )
    freshness_policy: dict[str, Any] = Field(
        alias="freshnessPolicy",
        description="Freshness class and max-age semantics declared for the product.",
    )
    completeness_policy: dict[str, Any] = Field(
        alias="completenessPolicy",
        description="Completeness posture and partial-data allowance declared for the product.",
    )
    lineage_policy: dict[str, Any] = Field(
        alias="lineagePolicy",
        description="Lineage and evidence requirements declared for the product.",
    )
    security_profile_ref: str = Field(
        alias="securityProfileRef",
        description="Reference to the governed security profile for product access.",
    )
    approved_consumers: list[str] = Field(
        alias="approvedConsumers",
        description="Repositories explicitly approved to consume this product.",
    )
    current_routes: list[str] = Field(
        alias="currentRoutes",
        description="Current producer API routes or access paths for the product.",
    )
    deprecation_policy: dict[str, Any] = Field(
        alias="deprecationPolicy",
        description="Deprecation state and successor product metadata.",
    )
    source_path: str = Field(
        alias="sourcePath",
        description="Platform declaration path from which this product was aggregated.",
    )

    model_config = {"populate_by_name": True}


class DomainProductDependency(BaseModel):
    dependency_id: str = Field(
        alias="dependencyId",
        description="Stable dependency identity, usually the required product id.",
    )
    product_name: str = Field(alias="productName", description="Required product name.")
    producer_repository: str = Field(
        alias="producerRepository",
        description="Repository that produces the required product.",
    )
    required_product_version: str = Field(
        alias="requiredProductVersion",
        description="Required product contract version.",
    )
    required_trust_metadata: list[str] = Field(
        alias="requiredTrustMetadata",
        description="Trust metadata the consumer requires for safe use.",
    )
    migration_posture: dict[str, Any] = Field(
        alias="migrationPosture",
        description="Consumer migration posture for the dependency.",
    )
    consumption_mode: str = Field(
        alias="consumptionMode",
        description="Declared consumption mode such as API read or paged API read.",
    )
    business_purpose: str = Field(
        alias="businessPurpose",
        description="Business reason the consumer depends on the product.",
    )
    validation_lanes: list[str] = Field(
        alias="validationLanes",
        description="Validation lanes that must cover this dependency.",
    )
    failure_posture: str = Field(
        alias="failurePosture",
        description="Consumer failure posture when the product is unavailable or untrusted.",
        examples=["fail_closed"],
    )
    failure_posture_conditions: list[DomainProductFailurePostureCondition] = Field(
        default_factory=list,
        alias="failurePostureConditions",
        description=(
            "Conditional failure-posture overrides that make the effective behavior "
            "discoverable for specific request situations."
        ),
    )

    model_config = {"populate_by_name": True}


class DomainProductConsumer(BaseModel):
    consumer_repository: str = Field(
        alias="consumerRepository",
        description="Repository declaring governed product dependencies.",
    )
    dependency_count: int = Field(
        alias="dependencyCount",
        description="Number of declared domain-product dependencies.",
    )
    source_path: str = Field(
        alias="sourcePath",
        description="Platform declaration path from which dependencies were aggregated.",
    )
    dependencies: list[DomainProductDependency] = Field(
        description="Governed product dependencies declared by this consumer."
    )

    model_config = {"populate_by_name": True}


class DomainProductCatalogData(BaseModel):
    consumer_system: str = Field(
        alias="consumerSystem",
        description="Caller identity used for gateway discovery and diagnostics.",
    )
    correlation_id: str = Field(
        alias="correlationId",
        description="Correlation id associated with this discovery response.",
    )
    contract_id: str = Field(alias="contractId", description="Platform catalog contract id.")
    contract_version: str = Field(
        alias="contractVersion",
        description="Platform catalog contract version.",
    )
    generated_at_utc: str = Field(
        alias="generatedAtUtc",
        description="UTC timestamp when the platform catalog artifact was generated.",
    )
    source_manifest_path: str = Field(
        alias="sourceManifestPath",
        description="Platform source manifest that governed catalog aggregation.",
    )
    governed_by_rfcs: list[str] = Field(
        alias="governedByRfcs",
        description="Platform RFCs that govern catalog generation and publication.",
    )
    source_declaration_directory: str = Field(
        alias="sourceDeclarationDirectory",
        description="Platform declaration directory aggregated into this catalog artifact.",
    )
    source_manifest: dict[str, Any] = Field(
        alias="sourceManifest",
        description="Source manifest snapshot included by the platform artifact.",
    )
    product_count: int = Field(
        alias="productCount",
        description="Number of products included in the platform catalog.",
    )
    dependency_count: int = Field(
        alias="dependencyCount",
        description="Number of declared consumer dependencies in the platform catalog.",
    )
    repository_count: int = Field(
        alias="repositoryCount",
        description="Number of producer repositories included in the catalog.",
    )
    repositories: list[DomainProductRepositorySummary] = Field(
        description="Producer and consumer repository summary counts."
    )
    products: list[DomainProduct] = Field(description="Governed domain products.")
    consumers: list[DomainProductConsumer] = Field(
        description="Governed product consumers and their dependencies."
    )

    model_config = {"populate_by_name": True}


class DomainProductCatalogResponse(BaseModel):
    data: DomainProductCatalogData = Field(
        description="Gateway discovery view over the platform-generated domain-product catalog."
    )


class DomainProductDetailData(BaseModel):
    consumer_system: str = Field(alias="consumerSystem", description="Caller identity.")
    correlation_id: str = Field(alias="correlationId", description="Correlation id.")
    contract_version: str = Field(
        alias="contractVersion",
        description="Platform catalog contract version used for the lookup.",
    )
    product: DomainProduct = Field(description="Matched governed domain product.")

    model_config = {"populate_by_name": True}


class DomainProductDetailResponse(BaseModel):
    data: DomainProductDetailData = Field(description="Matched domain-product detail.")
