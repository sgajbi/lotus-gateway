from fastapi.testclient import TestClient

from app.main import app


def test_domain_product_discovery_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    paths = spec["paths"]
    assert "/api/v1/domain-products/catalog" in paths
    product_path = (
        "/api/v1/domain-products/products/{producer_repository}/{product_name}/{product_version}"
    )
    assert product_path in paths
    assert "/api/v1/domain-products/dependency-graph" in paths
    assert "/api/v1/domain-products/trust-certification" in paths

    catalog_operation = paths["/api/v1/domain-products/catalog"]["get"]
    assert catalog_operation["summary"] == "Get Governed Domain Product Catalog"
    assert "platform-generated domain-product catalog" in catalog_operation["description"]
    assert "Gateway is only the discovery facade" in catalog_operation["description"]

    catalog_parameters = {
        parameter["name"]: parameter for parameter in catalog_operation["parameters"]
    }
    assert catalog_parameters["consumerSystem"]["schema"]["examples"] == [
        "lotus-workbench",
        "lotus-ai",
        "lotus-report",
    ]
    consumer_description = catalog_parameters["consumerSystem"]["schema"]["description"]
    assert "caller identity" in consumer_description.lower()
    assert catalog_parameters["X-Correlation-Id"]["description"]

    product_operation = paths[product_path]["get"]
    assert product_operation["summary"] == "Get Governed Domain Product Detail"
    assert "approved consumers" in product_operation["description"]

    graph_operation = paths["/api/v1/domain-products/dependency-graph"]["get"]
    assert graph_operation["summary"] == "Get Governed Domain Product Dependency Graph"
    assert "impact analysis" in graph_operation["description"]

    trust_operation = paths["/api/v1/domain-products/trust-certification"]["get"]
    assert trust_operation["summary"] == "Get Governed Domain Product Trust Certification"
    assert "platform-generated RFC-0087 live trust certification" in trust_operation["description"]
    assert "Gateway does not calculate product trust" in trust_operation["description"]


def test_domain_product_discovery_response_schemas_are_documented() -> None:
    client = TestClient(app)
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    catalog_data = schemas["DomainProductCatalogData"]
    product = schemas["DomainProduct"]
    dependency = schemas["DomainProductDependency"]
    graph_data = schemas["DomainProductGraphData"]
    graph_edge = schemas["DomainProductGraphEdge"]
    trust_data = schemas["DomainProductTrustCertificationData"]
    trust_summary = schemas["DomainProductLiveTrustSummary"]
    trust_product = schemas["DomainProductLiveTrustCertification"]
    trust_issue = schemas["DomainProductLiveTrustIssue"]

    assert catalog_data["properties"]["consumerSystem"]["description"]
    assert catalog_data["properties"]["governedByRfcs"]["description"]
    assert catalog_data["properties"]["sourceDeclarationDirectory"]["description"]
    assert catalog_data["properties"]["sourceManifest"]["description"]
    assert catalog_data["properties"]["products"]["description"]
    assert catalog_data["properties"]["consumers"]["description"]

    assert product["properties"]["productId"]["description"]
    assert product["properties"]["producerRepository"]["description"]
    assert product["properties"]["authoritativeDomain"]["description"]
    assert product["properties"]["requiredTrustMetadata"]["description"]
    assert product["properties"]["approvedConsumers"]["description"]
    assert product["properties"]["sourcePath"]["description"]

    assert dependency["properties"]["dependencyId"]["description"]
    assert dependency["properties"]["requiredTrustMetadata"]["description"]
    assert dependency["properties"]["validationLanes"]["description"]
    assert dependency["properties"]["failurePosture"]["examples"] == ["fail_closed"]

    assert graph_data["properties"]["nodes"]["description"]
    assert graph_data["properties"]["governedByRfcs"]["description"]
    assert graph_data["properties"]["edges"]["description"]
    assert graph_edge["properties"]["edgeType"]["description"]
    assert graph_edge["properties"]["failurePosture"]["description"]

    assert trust_data["properties"]["trustAvailable"]["description"]
    assert trust_data["properties"]["trustPosture"]["examples"] == [
        "certified",
        "attention_required",
        "unavailable",
    ]
    assert trust_data["properties"]["unavailableReason"]["description"]
    assert trust_data["properties"]["productCertifications"]["description"]
    assert trust_summary["properties"]["telemetrySnapshotCount"]["description"]
    assert trust_product["properties"]["producerRepository"]["description"]
    assert trust_product["properties"]["lineageMaterialized"]["description"]
    assert trust_issue["properties"]["productId"]["description"]
