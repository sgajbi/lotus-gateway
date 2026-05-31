from fastapi.testclient import TestClient

from app.contracts.domain_products import (
    DomainProductCatalogResponse,
    DomainProductDetailResponse,
    DomainProductGraphResponse,
    DomainProductTrustCertificationResponse,
)
from app.main import app
from app.services.domain_product_catalog_service import (
    DomainProductCatalogUnavailable,
    DomainProductNotFound,
)


def _catalog_response(consumer_system: str, correlation_id: str) -> DomainProductCatalogResponse:
    return DomainProductCatalogResponse.model_validate(
        {
            "data": {
                "consumerSystem": consumer_system,
                "correlationId": correlation_id,
                "contractId": "lotus-domain-product-catalog",
                "contractVersion": "1.0.0",
                "generatedAtUtc": "2026-04-19T00:00:00Z",
                "sourceManifestPath": "platform-contracts/domain-data-products/source.v1.json",
                "sourceManifest": {"repositories": []},
                "productCount": 1,
                "dependencyCount": 0,
                "repositoryCount": 1,
                "repositories": [
                    {
                        "repository": "lotus-core",
                        "producedProductCount": 1,
                        "consumedDependencyCount": 0,
                    }
                ],
                "products": [
                    {
                        "productId": "lotus-core:PortfolioStateSnapshot:v1",
                        "productName": "PortfolioStateSnapshot",
                        "productVersion": "v1",
                        "producerRepository": "lotus-core",
                        "ownerRepository": "lotus-core",
                        "authoritativeDomain": "portfolio_state",
                        "productFamily": "simulation_and_projected_state",
                        "lifecycleStatus": "active",
                        "requestScope": {"scope_level": "portfolio"},
                        "temporalScope": {"primary_time_field": "as_of_date"},
                        "temporalSemanticsRef": "as_of_date",
                        "identifierRefs": ["portfolio_id", "tenant_id"],
                        "requiredTrustMetadata": ["as_of_date", "data_quality_status"],
                        "freshnessPolicy": {"freshness_class": "daily"},
                        "completenessPolicy": {"default_status": "complete"},
                        "lineagePolicy": {"lineage_required": True},
                        "securityProfileRef": "system_access:reference_internal",
                        "approvedConsumers": ["lotus-gateway"],
                        "currentRoutes": ["/integration/portfolios/{portfolio_id}/state"],
                        "deprecationPolicy": {"state": "not_deprecated"},
                        "sourcePath": (
                            "platform-contracts/domain-data-products/lotus-core-products.v1.json"
                        ),
                    }
                ],
                "consumers": [],
            }
        }
    )


class _FakeDomainProductService:
    async def get_catalog(self, *, consumer_system: str, correlation_id: str):
        return _catalog_response(consumer_system, correlation_id)

    async def get_product(
        self,
        *,
        producer_repository: str,
        product_name: str,
        product_version: str,
        consumer_system: str,
        correlation_id: str,
    ):
        if product_name == "MissingProduct":
            raise DomainProductNotFound(f"{producer_repository}:{product_name}:{product_version}")
        catalog = _catalog_response(consumer_system, correlation_id)
        return DomainProductDetailResponse.model_validate(
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    "contractVersion": "1.0.0",
                    "product": catalog.data.products[0].model_dump(by_alias=True),
                }
            }
        )

    async def get_dependency_graph(self, *, consumer_system: str, correlation_id: str):
        return DomainProductGraphResponse.model_validate(
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    "contractId": "lotus-domain-product-dependency-graph",
                    "contractVersion": "1.0.0",
                    "generatedAtUtc": "2026-04-19T00:00:00Z",
                    "sourceCatalog": "domain-product-catalog.json",
                    "nodeCount": 2,
                    "edgeCount": 1,
                    "nodes": [
                        {
                            "nodeId": "repo:lotus-gateway",
                            "nodeType": "repository",
                            "repository": "lotus-gateway",
                        },
                        {
                            "nodeId": "product:lotus-core:PortfolioStateSnapshot:v1",
                            "nodeType": "domain_product",
                            "productId": "lotus-core:PortfolioStateSnapshot:v1",
                            "productName": "PortfolioStateSnapshot",
                            "productVersion": "v1",
                            "producerRepository": "lotus-core",
                            "productFamily": "simulation_and_projected_state",
                            "lifecycleStatus": "active",
                        },
                    ],
                    "edges": [
                        {
                            "edgeType": "approves_consumer",
                            "from": "product:lotus-core:PortfolioStateSnapshot:v1",
                            "to": "repo:lotus-gateway",
                        }
                    ],
                }
            }
        )

    async def get_trust_certification(self, *, consumer_system: str, correlation_id: str):
        return DomainProductTrustCertificationResponse.model_validate(
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    "trustAvailable": True,
                    "trustPosture": "attention_required",
                    "unavailableReason": None,
                    "contractId": "lotus-domain-product-live-trust-certification",
                    "contractVersion": "1.0.0",
                    "governedByRfcs": ["RFC-0087"],
                    "generatedAtUtc": "2026-04-19T00:00:00Z",
                    "sourceTelemetryPath": "contracts/trust-telemetry",
                    "summary": {
                        "certificationState": "attention_required",
                        "telemetrySnapshotCount": 1,
                        "certifiedSnapshotCount": 0,
                        "attentionRequiredCount": 1,
                        "issueCount": 1,
                    },
                    "productCertifications": [
                        {
                            "productId": "lotus-risk:RiskMetricsReport:v1",
                            "producerRepository": "lotus-risk",
                            "productName": "RiskMetricsReport",
                            "productVersion": "v1",
                            "sourceRepository": "lotus-risk",
                            "telemetryPath": (
                                "contracts/trust-telemetry/risk-metrics-report.telemetry.v1.json"
                            ),
                            "emittedAtUtc": "2026-04-19T00:00:00Z",
                            "certificationState": "attention_required",
                            "freshnessState": "stale",
                            "completenessStatus": "complete",
                            "reconciliationStatus": "reconciled",
                            "dataQualityStatus": "quality_passed",
                            "lineageMaterialized": True,
                            "blocked": False,
                            "issueCount": 1,
                        }
                    ],
                    "issues": [
                        {
                            "code": "freshness_not_current",
                            "severity": "warning",
                            "productId": "lotus-risk:RiskMetricsReport:v1",
                            "detail": "Freshness state is stale.",
                        }
                    ],
                }
            }
        )


def test_domain_product_catalog_router_preserves_consumer_and_correlation(monkeypatch):
    monkeypatch.setattr(
        "app.routers.domain_products.domain_product_catalog_service",
        lambda: _FakeDomainProductService(),
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/domain-products/catalog?consumerSystem=lotus-ai",
        headers={"X-Correlation-Id": "corr-domain-router-1"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["consumerSystem"] == "lotus-ai"
    assert data["correlationId"] == "corr-domain-router-1"
    assert data["products"][0]["productId"] == "lotus-core:PortfolioStateSnapshot:v1"
    assert data["products"][0]["approvedConsumers"] == ["lotus-gateway"]


def test_domain_product_detail_router_returns_full_identity_lookup(monkeypatch):
    monkeypatch.setattr(
        "app.routers.domain_product_detail.domain_product_catalog_service",
        lambda: _FakeDomainProductService(),
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/domain-products/products/lotus-core/PortfolioStateSnapshot/v1"
        "?consumerSystem=lotus-workbench"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["consumerSystem"] == "lotus-workbench"
    assert data["product"]["producerRepository"] == "lotus-core"
    assert data["product"]["productName"] == "PortfolioStateSnapshot"
    assert data["product"]["productVersion"] == "v1"


def test_domain_product_detail_router_does_not_fabricate_unknown_products(monkeypatch):
    monkeypatch.setattr(
        "app.routers.domain_product_detail.domain_product_catalog_service",
        lambda: _FakeDomainProductService(),
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/domain-products/products/lotus-core/MissingProduct/v1"
        "?consumerSystem=lotus-workbench"
    )

    assert response.status_code == 404
    assert "lotus-core:MissingProduct:v1" in response.json()["detail"]


def test_domain_product_graph_router_exposes_dependency_relationships(monkeypatch):
    monkeypatch.setattr(
        "app.routers.domain_product_graph.domain_product_catalog_service",
        lambda: _FakeDomainProductService(),
    )

    client = TestClient(app)
    response = client.get("/api/v1/domain-products/dependency-graph")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["contractId"] == "lotus-domain-product-dependency-graph"
    assert data["nodes"][0]["nodeId"] == "repo:lotus-gateway"
    assert data["edges"][0]["edgeType"] == "approves_consumer"


def test_domain_product_trust_router_exposes_certified_platform_posture(monkeypatch):
    monkeypatch.setattr(
        "app.routers.domain_product_trust.domain_product_catalog_service",
        lambda: _FakeDomainProductService(),
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/domain-products/trust-certification?consumerSystem=lotus-workbench",
        headers={"X-Correlation-Id": "corr-trust-router-1"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["consumerSystem"] == "lotus-workbench"
    assert data["correlationId"] == "corr-trust-router-1"
    assert data["trustAvailable"] is True
    assert data["trustPosture"] == "attention_required"
    assert data["summary"]["issueCount"] == 1
    assert data["productCertifications"][0]["productId"] == "lotus-risk:RiskMetricsReport:v1"
    assert data["issues"][0]["code"] == "freshness_not_current"


def test_domain_product_router_reports_platform_artifact_unavailable(monkeypatch):
    class _UnavailableService:
        async def get_catalog(self, *, consumer_system: str, correlation_id: str):
            raise DomainProductCatalogUnavailable("catalog artifact missing")

    monkeypatch.setattr(
        "app.routers.domain_products.domain_product_catalog_service",
        lambda: _UnavailableService(),
    )

    client = TestClient(app)
    response = client.get("/api/v1/domain-products/catalog")

    assert response.status_code == 503
    assert response.json()["detail"] == "catalog artifact missing"
