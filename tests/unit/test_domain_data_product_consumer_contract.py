import ast
import json
from pathlib import Path

import pytest

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "domain-data-products"
    / "lotus-gateway-consumers.v1.json"
)
CLIENT_ROOT = Path(__file__).resolve().parents[2] / "src" / "app" / "clients"
ROUTE_INVENTORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "domain-data-products"
    / "lotus-gateway-core-route-inventory.v1.json"
)


def _consumer_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _route_inventory() -> dict:
    return json.loads(ROUTE_INVENTORY_PATH.read_text(encoding="utf-8"))


# These are Core integration calls, but they are control-plane/snapshot operations rather
# than RFC-0084 domain-product reads. The explicit boundary is intentionally small: a new
# Core integration method not classified here is treated as a domain-product read and must be
# added to the route inventory before the contract gate can pass.
_NON_DOMAIN_PRODUCT_CORE_INTEGRATION_ROUTE_MARKERS = {
    "get_capabilities": ("/integration/capabilities",),
    "get_effective_policy": ("/integration/policy/effective",),
    "get_core_snapshot": ("core-snapshot",),
}


def _path_argument_literals(node: ast.AsyncFunctionDef) -> set[str]:
    return {
        constant.value
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        for keyword in call.keywords
        if keyword.arg == "path"
        for constant in ast.walk(keyword.value)
        if isinstance(constant, ast.Constant) and isinstance(constant.value, str)
    }


def _implemented_core_domain_product_reads(
    client_root: Path = CLIENT_ROOT,
) -> set[tuple[str, str]]:
    implemented: set[tuple[str, str]] = set()
    for client_path in sorted(client_root.glob("lotus_core*.py")):
        tree = ast.parse(client_path.read_text(encoding="utf-8"), filename=str(client_path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            path_literals = _path_argument_literals(node)
            if not any("/integration/" in literal for literal in path_literals):
                continue
            non_domain_markers = _NON_DOMAIN_PRODUCT_CORE_INTEGRATION_ROUTE_MARKERS.get(
                node.name, ()
            )
            if any(marker in literal for marker in non_domain_markers for literal in path_literals):
                continue
            implemented.add((client_path.name, node.name))
    return implemented


def _assert_implemented_core_reads_are_declared(client_root: Path = CLIENT_ROOT) -> None:
    declared = {
        (Path(route["client_module"]).name, route["client_method"])
        for route in _route_inventory()["routes"]
    }
    undeclared = _implemented_core_domain_product_reads(client_root) - declared
    if undeclared:
        details = ", ".join(
            f"{client_module}:{client_method}"
            for client_module, client_method in sorted(undeclared)
        )
        raise AssertionError(
            "Core integration reads missing from the RFC-0084 route inventory: " + details
        )


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
            "failure_posture": "fail_closed",
            "failure_posture_conditions": [
                {
                    "condition": (
                        "reference unavailable for a request that does not require inception "
                        "metadata"
                    ),
                    "posture": "degrade_to_partial",
                    "reason_codes": ["PERFORMANCE_REFERENCE_UNAVAILABLE"],
                    "behavior": (
                        "Preserve the bounded partial response and record the typed source failure."
                    ),
                },
                {
                    "condition": "Core reference lacks performance_end_date",
                    "posture": "degrade_to_partial",
                    "reason_codes": ["PERFORMANCE_REFERENCE_MISSING_END_DATE"],
                    "behavior": (
                        "Use the configured fallback reporting end date and expose the "
                        "PERFORMANCE_REFERENCE_MISSING_END_DATE warning; do not claim a "
                        "typed partial failure."
                    ),
                },
                {
                    "condition": (
                        "period=SI without explicit start and Core portfolio_open_date is "
                        "unavailable, invalid, or after the requested end date"
                    ),
                    "posture": "fail_closed",
                    "reason_codes": [
                        "PERFORMANCE_INCEPTION_UNAVAILABLE",
                        "PERFORMANCE_INCEPTION_AFTER_WINDOW_END",
                    ],
                    "behavior": (
                        "Return the typed performance window error and do not submit the "
                        "analytics request."
                    ),
                },
            ],
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
            "failure_posture_conditions": [
                {
                    "condition": (
                        "Core assignment lookup returns an HTTP error, invalid payload, or "
                        "unexpected transport exception"
                    ),
                    "posture": "degrade_to_partial",
                    "reason_codes": ["BENCHMARK_ASSIGNMENT_UNAVAILABLE"],
                    "behavior": (
                        "Preserve the bounded response without assuming an assignment; "
                        "append the warning and sanitized lotus-core partial failure."
                    ),
                }
            ],
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
    inventory = _route_inventory()
    inventory_products = {route["product_name"] for route in inventory["routes"]}

    assert inventory["contract_id"] == "lotus-gateway-core-direct-route-inventory"
    assert inventory["governed_by_rfc"] == "RFC-0084"
    assert inventory_products == contract_products

    for route_definition in inventory["routes"]:
        product_name = route_definition["product_name"]
        client_source = (CLIENT_ROOT / Path(route_definition["client_module"]).name).read_text(
            encoding="utf-8"
        )
        assert f"async def {route_definition['client_method']}" in client_source
        route_template = route_definition["route_template"]
        route_fragments = tuple(
            fragment.split("}", 1)[-1] for fragment in route_template.split("{") if fragment
        )
        for route_fragment in route_fragments:
            if route_fragment and route_fragment not in client_source:
                raise AssertionError(
                    f"{product_name} route fragment {route_fragment!r} is missing from "
                    f"{route_definition['client_module']}"
                )

    _assert_implemented_core_reads_are_declared()


def test_undeclared_core_integration_read_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "lotus_core_query_client.py").write_text(
        """
class FakeCoreClient:
    async def get_undeclared_product_read(self, portfolio_id: str):
        return await self._post_control_plane_resource(
            path=f"/integration/portfolios/{portfolio_id}/undeclared-product",
        )
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        AssertionError,
        match=(
            "Core integration reads missing from the RFC-0084 route inventory: "
            "lotus_core_query_client.py:get_undeclared_product_read"
        ),
    ):
        _assert_implemented_core_reads_are_declared(tmp_path)
