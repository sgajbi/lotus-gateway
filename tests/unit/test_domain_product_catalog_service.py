import json
from pathlib import Path
from typing import Any

import pytest

from app.services.domain_product_catalog_service import (
    DomainProductCatalogService,
    DomainProductCatalogUnavailable,
    DomainProductNotFound,
)


def _catalog_payload() -> dict[str, Any]:
    return {
        "contract_id": "lotus-domain-product-catalog",
        "contract_version": "1.0.0",
        "generated_at_utc": "2026-04-19T00:00:00Z",
        "source_manifest_path": "platform-contracts/domain-data-products/source.v1.json",
        "governed_by_rfcs": ["RFC-0084", "RFC-0086"],
        "source_declaration_directory": "platform-contracts/domain-data-products",
        "source_manifest": {"contract_id": "source", "repositories": []},
        "product_count": 1,
        "dependency_count": 1,
        "repository_count": 1,
        "repositories": [
            {
                "repository": "lotus-core",
                "produced_product_count": 1,
                "consumed_dependency_count": 0,
            }
        ],
        "products": [
            {
                "product_id": "lotus-core:PortfolioStateSnapshot:v1",
                "product_name": "PortfolioStateSnapshot",
                "product_version": "v1",
                "producer_repository": "lotus-core",
                "owner_repository": "lotus-core",
                "authoritative_domain": "portfolio_state",
                "product_family": "simulation_and_projected_state",
                "lifecycle_status": "active",
                "request_scope": {"scope_level": "portfolio"},
                "temporal_scope": {
                    "primary_time_field": "as_of_date",
                    "freshness_basis": "as_of_date",
                    "supports_restatement": True,
                },
                "temporal_semantics_ref": "as_of_date",
                "identifier_refs": ["portfolio_id", "tenant_id"],
                "required_trust_metadata": [
                    "product_name",
                    "product_version",
                    "as_of_date",
                    "data_quality_status",
                ],
                "freshness_policy": {"freshness_class": "daily"},
                "completeness_policy": {"default_status": "complete", "partial_allowed": False},
                "lineage_policy": {
                    "lineage_required": True,
                    "evidence_bundle_required": False,
                },
                "security_profile_ref": "system_access:reference_internal",
                "approved_consumers": ["lotus-risk", "lotus-gateway"],
                "current_routes": ["/integration/portfolios/{portfolio_id}/state"],
                "deprecation_policy": {"state": "not_deprecated", "successor_product": None},
                "source_path": (
                    "platform-contracts/domain-data-products/lotus-core-products.v1.json"
                ),
            }
        ],
        "consumers": [
            {
                "consumer_repository": "lotus-risk",
                "dependency_count": 1,
                "source_path": (
                    "platform-contracts/domain-data-products/lotus-risk-consumers.v1.json"
                ),
                "dependencies": [
                    {
                        "dependency_id": "lotus-core:PortfolioStateSnapshot:v1",
                        "product_name": "PortfolioStateSnapshot",
                        "producer_repository": "lotus-core",
                        "required_product_version": "v1",
                        "required_trust_metadata": ["as_of_date", "data_quality_status"],
                        "migration_posture": {"status": "current"},
                        "consumption_mode": "api_read",
                        "business_purpose": "Source risk analytics input state.",
                        "validation_lanes": ["feature", "pr-merge"],
                        "failure_posture": "fail_closed",
                    }
                ],
            }
        ],
    }


def _graph_payload() -> dict[str, Any]:
    return {
        "contract_id": "lotus-domain-product-dependency-graph",
        "contract_version": "1.0.0",
        "generated_at_utc": "2026-04-19T00:00:00Z",
        "source_catalog": "domain-product-catalog.json",
        "governed_by_rfcs": ["RFC-0084", "RFC-0086"],
        "node_count": 2,
        "edge_count": 1,
        "nodes": [
            {
                "node_id": "repo:lotus-risk",
                "node_type": "repository",
                "repository": "lotus-risk",
            },
            {
                "node_id": "product:lotus-core:PortfolioStateSnapshot:v1",
                "node_type": "domain_product",
                "product_id": "lotus-core:PortfolioStateSnapshot:v1",
                "product_name": "PortfolioStateSnapshot",
                "product_version": "v1",
                "producer_repository": "lotus-core",
                "product_family": "simulation_and_projected_state",
                "lifecycle_status": "active",
            },
        ],
        "edges": [
            {
                "edge_type": "consumes",
                "from": "repo:lotus-risk",
                "to": "product:lotus-core:PortfolioStateSnapshot:v1",
                "consumption_mode": "api_read",
                "failure_posture": "fail_closed",
                "validation_lanes": ["feature", "pr-merge"],
            }
        ],
    }


def _trust_certification_payload() -> dict[str, Any]:
    return {
        "contract_id": "lotus-domain-product-live-trust-certification",
        "contract_version": "1.0.0",
        "governed_by_rfcs": ["RFC-0087"],
        "generated_at_utc": "2026-04-19T00:00:00Z",
        "source_telemetry_path": "contracts/trust-telemetry",
        "summary": {
            "certification_state": "certified",
            "telemetry_snapshot_count": 1,
            "certified_snapshot_count": 1,
            "attention_required_count": 0,
            "issue_count": 0,
        },
        "product_certifications": [
            {
                "product_id": "lotus-core:PortfolioStateSnapshot:v1",
                "producer_repository": "lotus-core",
                "product_name": "PortfolioStateSnapshot",
                "product_version": "v1",
                "source_repository": "lotus-core",
                "telemetry_path": (
                    "contracts/trust-telemetry/portfolio-state-snapshot.telemetry.v1.json"
                ),
                "emitted_at_utc": "2026-04-19T00:00:00Z",
                "certification_state": "certified",
                "freshness_state": "current",
                "completeness_status": "complete",
                "reconciliation_status": "reconciled",
                "data_quality_status": "quality_passed",
                "lineage_materialized": True,
                "blocked": False,
                "issue_count": 0,
            }
        ],
        "issues": [],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _service_with_artifacts(tmp_path: Path) -> DomainProductCatalogService:
    catalog_path = tmp_path / "catalog.json"
    graph_path = tmp_path / "graph.json"
    trust_path = tmp_path / "trust.json"
    _write_json(catalog_path, _catalog_payload())
    _write_json(graph_path, _graph_payload())
    _write_json(trust_path, _trust_certification_payload())
    return DomainProductCatalogService(str(catalog_path), str(graph_path), str(trust_path))


@pytest.mark.asyncio
async def test_service_preserves_catalog_trust_and_dependency_context(tmp_path: Path) -> None:
    service = _service_with_artifacts(tmp_path)

    response = await service.get_catalog(
        consumer_system="lotus-workbench",
        correlation_id="corr-domain-products-1",
    )

    data = response.data
    assert data.consumer_system == "lotus-workbench"
    assert data.correlation_id == "corr-domain-products-1"
    assert data.contract_version == "1.0.0"
    assert data.governed_by_rfcs == ["RFC-0084", "RFC-0086"]
    assert data.source_declaration_directory == "platform-contracts/domain-data-products"
    assert data.products[0].product_id == "lotus-core:PortfolioStateSnapshot:v1"
    assert data.products[0].approved_consumers == ["lotus-risk", "lotus-gateway"]
    assert data.products[0].required_trust_metadata == [
        "product_name",
        "product_version",
        "as_of_date",
        "data_quality_status",
    ]
    assert data.consumers[0].dependencies[0].failure_posture == "fail_closed"
    assert data.consumers[0].dependencies[0].validation_lanes == ["feature", "pr-merge"]


@pytest.mark.asyncio
async def test_service_get_product_requires_full_governed_identity(tmp_path: Path) -> None:
    service = _service_with_artifacts(tmp_path)

    response = await service.get_product(
        producer_repository="lotus-core",
        product_name="PortfolioStateSnapshot",
        product_version="v1",
        consumer_system="lotus-ai",
        correlation_id="corr-product-1",
    )

    assert response.data.consumer_system == "lotus-ai"
    assert response.data.product.product_id == "lotus-core:PortfolioStateSnapshot:v1"
    assert response.data.product.source_path.endswith("lotus-core-products.v1.json")


@pytest.mark.asyncio
async def test_service_get_dependency_graph_preserves_consumption_posture(tmp_path: Path) -> None:
    service = _service_with_artifacts(tmp_path)

    response = await service.get_dependency_graph(
        consumer_system="lotus-platform",
        correlation_id="corr-graph-1",
    )

    assert response.data.node_count == 2
    assert response.data.governed_by_rfcs == ["RFC-0084", "RFC-0086"]
    assert response.data.edge_count == 1
    assert response.data.edges[0].edge_type == "consumes"
    assert response.data.edges[0].from_node == "repo:lotus-risk"
    assert response.data.edges[0].failure_posture == "fail_closed"


@pytest.mark.asyncio
async def test_service_exposes_live_trust_certification_without_recomputing_it(
    tmp_path: Path,
) -> None:
    service = _service_with_artifacts(tmp_path)

    response = await service.get_trust_certification(
        consumer_system="lotus-workbench",
        correlation_id="corr-trust-1",
    )

    data = response.data
    assert data.trust_available is True
    assert data.trust_posture == "certified"
    assert data.contract_id == "lotus-domain-product-live-trust-certification"
    assert data.summary is not None
    assert data.summary.telemetry_snapshot_count == 1
    assert data.product_certifications[0].product_id == ("lotus-core:PortfolioStateSnapshot:v1")
    assert data.product_certifications[0].lineage_materialized is True


@pytest.mark.asyncio
async def test_service_returns_explicit_unavailable_posture_when_live_trust_is_missing(
    tmp_path: Path,
) -> None:
    catalog_path = tmp_path / "catalog.json"
    graph_path = tmp_path / "graph.json"
    _write_json(catalog_path, _catalog_payload())
    _write_json(graph_path, _graph_payload())

    service = DomainProductCatalogService(
        str(catalog_path),
        str(graph_path),
        str(tmp_path / "missing-live-trust.json"),
    )

    response = await service.get_trust_certification(
        consumer_system="lotus-workbench",
        correlation_id="corr-trust-missing-1",
    )

    data = response.data
    assert data.trust_available is False
    assert data.trust_posture == "unavailable"
    assert data.unavailable_reason == "live_trust_certification_unavailable"
    assert str(tmp_path) not in str(data.unavailable_reason)
    assert data.product_certifications == []
    assert data.governed_by_rfcs == ["RFC-0087"]


@pytest.mark.asyncio
async def test_service_unknown_product_is_not_fabricated(tmp_path: Path) -> None:
    service = _service_with_artifacts(tmp_path)

    with pytest.raises(DomainProductNotFound, match="lotus-risk:MissingProduct:v1"):
        await service.get_product(
            producer_repository="lotus-risk",
            product_name="MissingProduct",
            product_version="v1",
            consumer_system="lotus-workbench",
            correlation_id="corr-missing-1",
        )


@pytest.mark.asyncio
async def test_service_reports_unavailable_platform_artifact(tmp_path: Path) -> None:
    service = DomainProductCatalogService(
        str(tmp_path / "missing-catalog.json"),
        str(tmp_path / "missing-graph.json"),
        str(tmp_path / "missing-trust.json"),
    )

    with pytest.raises(DomainProductCatalogUnavailable, match="catalog artifact is unavailable"):
        await service.get_catalog(
            consumer_system="lotus-workbench",
            correlation_id="corr-unavailable-1",
        )


@pytest.mark.asyncio
async def test_service_failure_messages_do_not_expose_configured_artifact_paths(
    tmp_path: Path,
) -> None:
    missing_catalog = tmp_path / "private-user" / "missing-catalog.json"
    service = DomainProductCatalogService(
        str(missing_catalog),
        str(tmp_path / "missing-graph.json"),
        str(tmp_path / "missing-trust.json"),
    )

    with pytest.raises(DomainProductCatalogUnavailable) as exc_info:
        await service.get_catalog(
            consumer_system="lotus-workbench",
            correlation_id="corr-path-safe-1",
        )

    detail = str(exc_info.value)
    assert detail == "Platform domain-product catalog artifact is unavailable."
    assert "private-user" not in detail
    assert "missing-catalog.json" not in detail


@pytest.mark.asyncio
async def test_service_reports_platform_artifact_contract_drift(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    graph_path = tmp_path / "graph.json"
    _write_json(catalog_path, {"contract_id": "lotus-domain-product-catalog"})
    _write_json(graph_path, _graph_payload())

    service = DomainProductCatalogService(
        str(catalog_path),
        str(graph_path),
        str(tmp_path / "trust.json"),
    )

    with pytest.raises(DomainProductCatalogUnavailable, match="contract validation"):
        await service.get_catalog(
            consumer_system="lotus-workbench",
            correlation_id="corr-contract-drift-1",
        )


@pytest.mark.asyncio
async def test_service_reports_live_trust_artifact_contract_drift(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    graph_path = tmp_path / "graph.json"
    trust_path = tmp_path / "trust.json"
    _write_json(catalog_path, _catalog_payload())
    _write_json(graph_path, _graph_payload())
    _write_json(
        trust_path,
        {
            **_trust_certification_payload(),
            "summary": {"telemetry_snapshot_count": 1},
        },
    )

    service = DomainProductCatalogService(str(catalog_path), str(graph_path), str(trust_path))

    with pytest.raises(DomainProductCatalogUnavailable, match="contract validation"):
        await service.get_trust_certification(
            consumer_system="lotus-workbench",
            correlation_id="corr-trust-contract-drift-1",
        )
