import json
from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "domain-data-products"
    / "lotus-gateway-consumers.v1.json"
)
CLIENT_ROOT = Path(__file__).resolve().parents[2] / "src" / "app" / "clients"

# This is intentionally an implementation-backed inventory rather than a prose copy of RFC-0082:
# each entry names the client method and route fragments that prove the declared Core product is
# still directly consumed by Gateway.  A missing method/route or an undeclared product fails the
# contract test before federation can publish a stale dependency edge.
IMPLEMENTED_CORE_ROUTE_INVENTORY = {
    "PortfolioManagerBookMembership": {
        "client": "lotus_core_portfolio_query_client.py",
        "method": "get_portfolio_manager_book_memberships",
        "route_fragments": (
            "/integration/portfolio-manager-books/",
            "/memberships",
        ),
    },
    "PortfolioAnalyticsReference": {
        "client": "lotus_core_query_client.py",
        "method": "get_portfolio_analytics_reference",
        "route_fragments": ("/integration/portfolios/", "/analytics/reference"),
    },
    "BenchmarkAssignment": {
        "client": "lotus_core_query_client.py",
        "method": "get_benchmark_assignment",
        "route_fragments": ("/integration/portfolios/", "/benchmark-assignment"),
    },
    "BenchmarkDefinition": {
        "client": "lotus_core_query_client.py",
        "method": "get_benchmark_catalog",
        "route_fragments": ("/integration/benchmarks/catalog",),
    },
    "ExternalOrderExecutionAcknowledgement": {
        "client": "lotus_core_query_client.py",
        "method": "get_external_order_execution_acknowledgement",
        "route_fragments": (
            "/integration/portfolios/",
            "/external-order-execution-acknowledgement",
        ),
    },
}


def _consumer_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_gateway_declares_only_implemented_rfc_0084_dependencies() -> None:
    contract = _consumer_contract()

    assert contract["contract_id"] == "domain-data-product-consumers"
    assert contract["contract_version"] == "1.0.0"
    assert contract["governed_by_rfc"] == "RFC-0084"
    assert contract["consumer_repository"] == "lotus-gateway"
    expected_dependencies = [
        {
            "product_name": "PortfolioManagerBookMembership",
            "producer_repository": "lotus-core",
            "required_product_version": "v1",
            "consumption_mode": "api_read",
            "business_purpose": (
                "Resolve the trusted caller's effective own-book portfolio memberships for the "
                "product-facing advisor-book facade without moving assignment ownership into "
                "Gateway."
            ),
            "validation_lanes": ["feature", "pr-merge", "platform-end-to-end"],
            "failure_posture": "fail_closed",
            "required_trust_metadata": [
                "product_name",
                "product_version",
                "portfolio_manager_id",
                "booking_center_code",
                "generated_at",
                "as_of_date",
                "data_quality_status",
                "source_evidence_current",
                "freshness_status",
                "content_hash",
            ],
            "migration_posture": {"status": "current"},
        },
        {
            "product_name": "PortfolioAnalyticsReference",
            "producer_repository": "lotus-core",
            "required_product_version": "v1",
            "consumption_mode": "api_read",
            "business_purpose": (
                "Resolve Core-owned portfolio analytics reference dates and lifecycle context for "
                "Gateway Workbench and performance composition without calculating analytics or "
                "owning portfolio state."
            ),
            "validation_lanes": ["feature", "pr-merge", "platform-end-to-end"],
            "failure_posture": "degrade_to_partial",
            "required_trust_metadata": [
                "product_name",
                "product_version",
                "generated_at",
                "as_of_date",
                "reconciliation_status",
                "data_quality_status",
                "correlation_id",
            ],
            "migration_posture": {"status": "current"},
        },
        {
            "product_name": "BenchmarkAssignment",
            "producer_repository": "lotus-core",
            "required_product_version": "v1",
            "consumption_mode": "api_read",
            "business_purpose": (
                "Resolve Core-owned effective portfolio benchmark assignment for Gateway "
                "performance and workspace responses without defining benchmark methodology or "
                "moving assignment ownership into Gateway."
            ),
            "validation_lanes": ["feature", "pr-merge", "platform-end-to-end"],
            "failure_posture": "degrade_to_partial",
            "required_trust_metadata": [
                "product_name",
                "product_version",
                "generated_at",
                "as_of_date",
                "data_quality_status",
                "correlation_id",
            ],
            "migration_posture": {"status": "current"},
        },
        {
            "product_name": "BenchmarkDefinition",
            "producer_repository": "lotus-core",
            "required_product_version": "v1",
            "consumption_mode": "api_read",
            "business_purpose": (
                "Resolve Core-owned benchmark catalog and definition records for Gateway "
                "benchmark-aware performance responses without owning benchmark master or "
                "constituent evidence."
            ),
            "validation_lanes": ["feature", "pr-merge", "platform-end-to-end"],
            "failure_posture": "degrade_to_partial",
            "required_trust_metadata": [
                "product_name",
                "product_version",
                "generated_at",
                "as_of_date",
                "data_quality_status",
                "correlation_id",
            ],
            "migration_posture": {"status": "current"},
        },
        {
            "product_name": "ExternalOrderExecutionAcknowledgement",
            "producer_repository": "lotus-core",
            "required_product_version": "v1",
            "consumption_mode": "supportability_lookup",
            "business_purpose": (
                "Preserve Core-owned fail-closed external OMS acknowledgement supportability "
                "through Gateway without generating orders, claiming fills or settlement, or "
                "asserting OMS ingestion."
            ),
            "validation_lanes": ["feature", "pr-merge", "platform-end-to-end"],
            "failure_posture": "fail_closed",
            "required_trust_metadata": [
                "product_name",
                "product_version",
                "as_of_date",
                "data_quality_status",
                "latest_evidence_timestamp",
                "source_batch_fingerprint",
                "correlation_id",
            ],
            "migration_posture": {"status": "current"},
        },
    ]

    assert contract["dependencies"] == expected_dependencies


def test_gateway_declarations_match_implemented_core_route_inventory() -> None:
    contract_products = {
        dependency["product_name"] for dependency in _consumer_contract()["dependencies"]
    }

    assert contract_products == set(IMPLEMENTED_CORE_ROUTE_INVENTORY)

    for product_name, route_definition in IMPLEMENTED_CORE_ROUTE_INVENTORY.items():
        client_source = (CLIENT_ROOT / route_definition["client"]).read_text(encoding="utf-8")
        assert f"async def {route_definition['method']}" in client_source
        for route_fragment in route_definition["route_fragments"]:
            assert route_fragment in client_source, (
                f"{product_name} route fragment {route_fragment!r} is missing from "
                f"{route_definition['client']}"
            )
