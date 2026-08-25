import ast
import json
import re
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
_ROUTE_TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]*\}")
_UNRESOLVED_ROUTE_TEMPLATE = "<unresolved integration route>"
_ROUTE_ARGUMENT_NAMES = frozenset({"path", "url"})
_CORE_CLIENT_ROUTE_VISIBILITY_EXEMPTIONS = {
    "lotus_core_transaction_params.py": "parameter and DTO definitions only; no transport calls",
}
_UNRESOLVED_CORE_CLIENT_ROUTE_EXEMPTIONS = {
    (
        "lotus_core_ingestion_client.py",
        "_upload",
    ): "generic upload transport composes the base URL with a caller-supplied path",
    (
        "lotus_core_lookup_client.py",
        "_get_lookup",
    ): "generic lookup transport forwards a caller-supplied path to the query helper",
    (
        "lotus_core_query_client.py",
        "_get_query_resource",
    ): "generic query transport composes the query base URL with a caller-supplied path",
    (
        "lotus_core_query_client.py",
        "_post_query_resource",
    ): "generic query transport composes the query base URL with a caller-supplied path",
    (
        "lotus_core_query_client.py",
        "_get_control_plane_resource",
    ): "generic control-plane transport composes its base URL with a caller-supplied path",
    (
        "lotus_core_query_client.py",
        "_post_control_plane_resource",
    ): "generic control-plane transport composes its base URL with a caller-supplied path",
    (
        "lotus_core_query_client.py",
        "_request",
    ): "generic HTTP transport receives its URL from the caller-supplied helper route",
}
_UNRESOLVED_CORE_CLIENT_ROUTE_EXEMPTION_SHAPES = {
    ("lotus_core_ingestion_client.py", "_upload"): ("base_url_plus_path", "_base_url"),
    ("lotus_core_lookup_client.py", "_get_lookup"): ("caller_path", None),
    ("lotus_core_query_client.py", "_get_query_resource"): (
        "base_url_plus_path",
        "_query_base_url",
    ),
    ("lotus_core_query_client.py", "_post_query_resource"): (
        "base_url_plus_path",
        "_query_base_url",
    ),
    ("lotus_core_query_client.py", "_get_control_plane_resource"): (
        "base_url_plus_path",
        "_control_plane_base_url",
    ),
    ("lotus_core_query_client.py", "_post_control_plane_resource"): (
        "base_url_plus_path",
        "_control_plane_base_url",
    ),
    ("lotus_core_query_client.py", "_request"): ("caller_url", None),
}


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


def _assignment_values(tree: ast.AST) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    nodes = tree.body if isinstance(tree, ast.Module) else ast.walk(tree)
    for node in nodes:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = node.value
    return assignments


def _resolve_route_templates(
    expression: ast.AST,
    assignments: dict[str, ast.AST],
    resolving: frozenset[str] = frozenset(),
    own_parameters: frozenset[str] = frozenset(),
    quote_provenance_is_safe: bool = False,
) -> set[str]:
    if isinstance(expression, ast.Name):
        if expression.id in resolving or expression.id not in assignments:
            return set()
        return _resolve_route_templates(
            assignments[expression.id],
            assignments,
            resolving | {expression.id},
            own_parameters,
            quote_provenance_is_safe,
        )
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return {expression.value}
    if isinstance(expression, ast.JoinedStr):
        template = ""
        for value in expression.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                template += value.value
            elif isinstance(value, ast.FormattedValue):
                if _route_interpolation_is_opaque(
                    value.value,
                    own_parameters,
                    assignments,
                    quote_provenance_is_safe=quote_provenance_is_safe,
                ) or (
                    value.format_spec is not None
                    and _route_interpolation_is_opaque(
                        value.format_spec,
                        own_parameters,
                        assignments,
                        quote_provenance_is_safe=quote_provenance_is_safe,
                    )
                ):
                    return set()
                template += "{}"
            else:
                return set()
        return {template}
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        left_templates = _resolve_route_templates(
            expression.left,
            assignments,
            resolving,
            own_parameters,
            quote_provenance_is_safe,
        )
        right_templates = _resolve_route_templates(
            expression.right,
            assignments,
            resolving,
            own_parameters,
            quote_provenance_is_safe,
        )
        return {left + right for left in left_templates for right in right_templates}
    if (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Attribute)
        and expression.func.attr == "format"
    ):
        replacements = [
            *expression.args,
            *(keyword.value for keyword in expression.keywords),
        ]
        if any(
            _route_interpolation_is_opaque(
                replacement,
                own_parameters,
                assignments,
                quote_provenance_is_safe=quote_provenance_is_safe,
            )
            for replacement in replacements
        ):
            return set()
        return _resolve_route_templates(
            expression.func.value,
            assignments,
            resolving,
            own_parameters,
            quote_provenance_is_safe,
        )
    return set()


def _resolves_to_empty_string(
    expression: ast.AST,
    assignments: dict[str, ast.AST],
    resolving: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(expression, ast.Constant):
        return expression.value == ""
    if isinstance(expression, ast.Name):
        if expression.id in resolving or expression.id not in assignments:
            return False
        return _resolves_to_empty_string(
            assignments[expression.id], assignments, resolving | {expression.id}
        )
    return False


def _target_binds_name(target: ast.AST, name: str) -> bool:
    return any(isinstance(node, ast.Name) and node.id == name for node in ast.walk(target))


def _quote_provenance_is_safe(tree: ast.Module) -> bool:
    trusted_import = False
    rebound = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for imported in node.names:
                bound_name = imported.asname or imported.name.split(".", maxsplit=1)[0]
                if (
                    node.module == "urllib.parse"
                    and imported.name == "quote"
                    and bound_name == "quote"
                ):
                    trusted_import = True
                elif bound_name == "quote":
                    rebound = True
        elif isinstance(node, ast.Import):
            for imported in node.names:
                bound_name = imported.asname or imported.name.split(".", maxsplit=1)[0]
                if bound_name == "quote":
                    rebound = True
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            rebound |= node.name == "quote"
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            rebound |= any(_target_binds_name(target, "quote") for target in targets)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            rebound |= _target_binds_name(node.target, "quote")
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            rebound |= any(
                item.optional_vars is not None and _target_binds_name(item.optional_vars, "quote")
                for item in node.items
            )
        elif isinstance(node, ast.ExceptHandler):
            rebound |= node.name == "quote"
        elif isinstance(node, ast.comprehension):
            rebound |= _target_binds_name(node.target, "quote")
        elif isinstance(node, ast.MatchAs):
            rebound |= node.name == "quote"
    return trusted_import and not rebound


def _route_interpolation_is_opaque(
    expression: ast.AST,
    own_parameters: frozenset[str],
    assignments: dict[str, ast.AST],
    resolving: frozenset[str] = frozenset(),
    *,
    quote_provenance_is_safe: bool = False,
    allow_unencoded_path: bool = True,
) -> bool:
    if isinstance(expression, ast.Call):
        if isinstance(expression.func, ast.Name) and expression.func.id == "quote":
            if "quote" in own_parameters or not quote_provenance_is_safe:
                return True
            safe_keyword = next(
                (keyword for keyword in expression.keywords if keyword.arg == "safe"),
                None,
            )
            if (
                safe_keyword is None
                or not _resolves_to_empty_string(safe_keyword.value, assignments)
                or any(keyword.arg is None for keyword in expression.keywords)
            ):
                return True
            arguments = [
                *expression.args,
                *(keyword.value for keyword in expression.keywords if keyword is not safe_keyword),
            ]
            return any(
                _route_interpolation_is_opaque(
                    argument,
                    own_parameters,
                    assignments,
                    resolving,
                    quote_provenance_is_safe=quote_provenance_is_safe,
                    allow_unencoded_path=False,
                )
                for argument in arguments
            )
        return True
    if isinstance(expression, ast.Name):
        if expression.id in own_parameters:
            return allow_unencoded_path and expression.id in {"path", "url"}
        if expression.id in resolving or expression.id not in assignments:
            return True
        return _route_interpolation_is_opaque(
            assignments[expression.id],
            own_parameters,
            assignments,
            resolving | {expression.id},
            quote_provenance_is_safe=quote_provenance_is_safe,
            allow_unencoded_path=allow_unencoded_path,
        )
    if isinstance(expression, ast.Constant):
        return False
    if isinstance(expression, ast.Attribute):
        return not (isinstance(expression.value, ast.Name) and expression.value.id == "self")
    if isinstance(expression, ast.Subscript):
        return _route_interpolation_is_opaque(
            expression.value,
            own_parameters,
            assignments,
            resolving,
            quote_provenance_is_safe=quote_provenance_is_safe,
            allow_unencoded_path=allow_unencoded_path,
        ) or _route_interpolation_is_opaque(
            expression.slice,
            own_parameters,
            assignments,
            resolving,
            quote_provenance_is_safe=quote_provenance_is_safe,
            allow_unencoded_path=allow_unencoded_path,
        )
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        return _route_interpolation_is_opaque(
            expression.left,
            own_parameters,
            assignments,
            resolving,
            quote_provenance_is_safe=quote_provenance_is_safe,
            allow_unencoded_path=allow_unencoded_path,
        ) or _route_interpolation_is_opaque(
            expression.right,
            own_parameters,
            assignments,
            resolving,
            quote_provenance_is_safe=quote_provenance_is_safe,
            allow_unencoded_path=allow_unencoded_path,
        )
    return True


def _route_argument_templates(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    assignments: dict[str, ast.AST],
    quote_provenance_is_safe: bool = False,
) -> list[tuple[ast.AST, set[str], bool]]:
    routes: list[tuple[ast.AST, set[str], bool]] = []
    own_parameters = _function_parameter_names(node)
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        for keyword in call.keywords:
            if keyword.arg not in _ROUTE_ARGUMENT_NAMES:
                continue
            resolved = _resolve_route_templates(
                keyword.value,
                assignments,
                own_parameters=own_parameters,
                quote_provenance_is_safe=quote_provenance_is_safe,
            )
            unresolved = not resolved or not any(
                _has_concrete_route_segment(route_template) for route_template in resolved
            )
            routes.append((keyword.value, resolved, unresolved))
    return routes


def _normalize_route_template(route_template: str) -> str:
    return _ROUTE_TEMPLATE_PLACEHOLDER_PATTERN.sub("{}", route_template)


def _integration_route_template(route_template: str) -> str | None:
    marker = "/integration/"
    route_start = route_template.find(marker)
    if route_start < 0:
        return None
    return route_template[route_start:]


def _has_concrete_route_segment(route_template: str) -> bool:
    return re.search(r"/[A-Za-z0-9]", route_template) is not None


def _function_parameter_names(node: ast.AsyncFunctionDef | ast.FunctionDef) -> frozenset[str]:
    arguments = node.args
    parameter_names = {
        argument.arg
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        )
    }
    if arguments.vararg is not None:
        parameter_names.add(arguments.vararg.arg)
    if arguments.kwarg is not None:
        parameter_names.add(arguments.kwarg.arg)
    parameter_names.difference_update({"self", "cls"})
    return frozenset(parameter_names)


def _route_expression_matches_allowlist_shape(
    client_module: str,
    client_method: str,
    expression: ast.AST,
    own_parameters: frozenset[str],
) -> bool:
    shape = _UNRESOLVED_CORE_CLIENT_ROUTE_EXEMPTION_SHAPES.get((client_module, client_method))
    if shape is None:
        return False
    shape_name, base_url_attribute = shape
    if shape_name == "caller_path":
        return (
            isinstance(expression, ast.Name)
            and expression.id == "path"
            and "path" in own_parameters
        )
    if shape_name == "caller_url":
        return (
            isinstance(expression, ast.Name) and expression.id == "url" and "url" in own_parameters
        )
    if shape_name == "base_url_plus_path":
        if not isinstance(expression, ast.JoinedStr) or len(expression.values) != 2:
            return False
        base_value, path_value = expression.values
        return (
            isinstance(base_value, ast.FormattedValue)
            and isinstance(base_value.value, ast.Attribute)
            and isinstance(base_value.value.value, ast.Name)
            and base_value.value.value.id == "self"
            and base_value.value.attr == base_url_attribute
            and isinstance(path_value, ast.FormattedValue)
            and isinstance(path_value.value, ast.Name)
            and path_value.value.id == "path"
            and "path" in own_parameters
        )
    return False


def _core_client_route_templates(tree: ast.Module) -> set[str]:
    routes: set[str] = set()
    module_assignments = _assignment_values(tree)
    quote_provenance_is_safe = _quote_provenance_is_safe(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        assignments = module_assignments | _assignment_values(node)
        for _, route_templates, _ in _route_argument_templates(
            node,
            assignments,
            quote_provenance_is_safe=quote_provenance_is_safe,
        ):
            routes.update(route for route in route_templates if _has_concrete_route_segment(route))
    return routes


def _assert_core_client_route_visibility(client_root: Path = CLIENT_ROOT) -> None:
    uncovered_modules: list[str] = []
    for client_path in sorted(client_root.glob("lotus_core*.py")):
        if client_path.name in _CORE_CLIENT_ROUTE_VISIBILITY_EXEMPTIONS:
            continue
        tree = ast.parse(
            client_path.read_text(encoding="utf-8"),
            filename=str(client_path),
        )
        if not _core_client_route_templates(tree):
            uncovered_modules.append(client_path.name)
    if uncovered_modules:
        details = ", ".join(uncovered_modules)
        raise AssertionError(
            "Core client modules without a statically resolvable transport route: " + details
        )


def _implemented_core_domain_product_reads(
    client_root: Path = CLIENT_ROOT,
) -> set[tuple[str, str, str]]:
    implemented: set[tuple[str, str, str]] = set()
    for client_path in sorted(client_root.glob("lotus_core*.py")):
        source = client_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(client_path))
        module_assignments = _assignment_values(tree)
        quote_provenance_is_safe = _quote_provenance_is_safe(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            assignments = module_assignments | _assignment_values(node)
            non_domain_markers = _NON_DOMAIN_PRODUCT_CORE_INTEGRATION_ROUTE_MARKERS.get(
                node.name, ()
            )
            for route_expression, route_templates, unresolved_route in _route_argument_templates(
                node,
                assignments,
                quote_provenance_is_safe=quote_provenance_is_safe,
            ):
                integration_routes = {
                    route
                    for template in route_templates
                    if (route := _integration_route_template(template)) is not None
                }
                if not integration_routes and not unresolved_route:
                    continue
                if unresolved_route:
                    if (
                        (client_path.name, node.name) in _UNRESOLVED_CORE_CLIENT_ROUTE_EXEMPTIONS
                        and _route_expression_matches_allowlist_shape(
                            client_path.name,
                            node.name,
                            route_expression,
                            _function_parameter_names(node),
                        )
                    ):
                        continue
                    implemented.add((client_path.name, node.name, _UNRESOLVED_ROUTE_TEMPLATE))
                    continue
                for route_template in integration_routes:
                    if any(marker in route_template for marker in non_domain_markers):
                        continue
                    implemented.add(
                        (client_path.name, node.name, _normalize_route_template(route_template))
                    )
    return implemented


def _assert_implemented_core_reads_are_declared(client_root: Path = CLIENT_ROOT) -> None:
    declared = {
        (
            Path(route["client_module"]).name,
            route["client_method"],
            _normalize_route_template(route["route_template"]),
        )
        for route in _route_inventory()["routes"]
    }
    undeclared = _implemented_core_domain_product_reads(client_root) - declared
    if undeclared:
        details = ", ".join(
            f"{client_module}:{client_method} [{route_template}]"
            for client_module, client_method, route_template in sorted(undeclared)
        )
        raise AssertionError(
            "Core integration reads missing from the RFC-0084 route inventory: " + details
        )
    _assert_core_client_route_visibility(client_root)


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
UNDECLARED_MODULE_ROUTE = "/integration/benchmarks/undeclared-product"
UNDECLARED_FORMAT_ROUTE = "/integration/portfolios/{portfolio_id}/undeclared-formatted"

class FakeCoreClient:
    async def get_undeclared_local_product_read(self, portfolio_id: str):
        route = f"/integration/portfolios/{portfolio_id}/undeclared-product"
        return await self._post_control_plane_resource(
            path=route,
        )

    async def get_undeclared_module_product_read(self):
        return await self._post_control_plane_resource(
            path=UNDECLARED_MODULE_ROUTE,
        )

    async def get_undeclared_format_product_read(self, portfolio_id: str):
        return await self._post_control_plane_resource(
            path=UNDECLARED_FORMAT_ROUTE.format(portfolio_id=portfolio_id),
        )
""".strip()
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError) as exc_info:
        _assert_implemented_core_reads_are_declared(tmp_path)

    message = str(exc_info.value)
    assert "lotus_core_query_client.py:get_undeclared_local_product_read" in message
    assert "lotus_core_query_client.py:get_undeclared_module_product_read" in message
    assert "lotus_core_query_client.py:get_undeclared_format_product_read" in message


def test_alternate_url_and_sync_core_reads_fail_closed(tmp_path: Path) -> None:
    (tmp_path / "lotus_core_url_client.py").write_text(
        """
class FakeCoreClient:
    async def get_undeclared_url_product_read(self):
        url = f"{self._base_url}/integration/products/undeclared-url"
        return await self._request(url=url)

    def get_undeclared_sync_product_read(self):
        return self._request(url="/integration/products/undeclared-sync")
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as exc_info:
        _assert_implemented_core_reads_are_declared(tmp_path)

    message = str(exc_info.value)
    assert "lotus_core_url_client.py:get_undeclared_sync_product_read" in message
    assert "lotus_core_url_client.py:get_undeclared_url_product_read" in message


def test_private_helper_route_exemption_requires_caller_supplied_expression(
    tmp_path: Path,
) -> None:
    (tmp_path / "lotus_core_private_helper_client.py").write_text(
        """
from urllib.parse import quote

HIDDEN_ROUTE_PREFIX = "/integration/hidden-product/"

class FakeCoreClient:
    async def get_capabilities(self):
        return await self._request(url="/integration/capabilities")

    async def _get_parameter_route(self, path):
        return await self._request(url=path)

    async def _get_parameter_alias(self, path):
        route = path
        return await self._request(url=route)

    async def _get_parameter_concat(self, path):
        return await self._request(url=path + "/suffix")

    async def _get_parameter_fstring(self, path):
        url = f"{self._base_url}{path}"
        return await self._request(url=url)

    async def _get_parameter_varargs(self, *routes, **options):
        route = routes[0] + options["suffix"]
        return await self._request(url=route)

    async def _get_internal_route(self, path):
        return await self._request(url=build_route(path))

    async def _get_mixed_internal_route(self, path):
        return await self._request(url=path + build_route(path))

    async def _get_fstring_internal_route(self, path):
        return await self._request(url=f"{build_route(path)}{path}")

    async def _get_resolved_opaque_fstring_route(self, path):
        return await self._request(url=f"{build_route(path)}/suffix")

    async def _get_bare_path_route(self, path):
        return await self._request(url=f"{path}/suffix")

    async def _get_format_internal_route(self, path):
        return await self._request(url="{}/suffix".format(build_route(path)))

    async def _get_default_quote_route(self, path):
        return await self._request(url=f"{quote(path)}/suffix")

    async def _get_safe_quote_route(self, path):
        return await self._request(url=f"{quote(path, safe='')}/suffix")

    async def _get_shadowed_quote_route(self, path, quote):
        return await self._request(url=f"{quote(path, safe='')}/suffix")

    async def _get_assigned_internal_route(self, path):
        route = build_route(path)
        return await self._request(url=route + path)

    async def _get_reassigned_alias_route(self, path):
        route = path
        await self._request(url=route)
        route = build_route(path)
        return await self._request(url=route)

    async def _get_attribute_route(self, path):
        return await self._request(url=self._hidden_integration_route + path)

    async def _get_namespace_attribute_route(self, path):
        return await self._request(url=ROUTES.hidden + path)

    async def _get_literal_route(self, suffix):
        return await self._request(url=HIDDEN_ROUTE_PREFIX + suffix)

    async def _get_split_literal_route(self, suffix):
        return await self._request(url="/integ" + "ration/hidden/" + suffix)

    async def _get_namespace_boundary_route(self, suffix):
        return await self._request(url="/integration" + suffix)

    async def _get_literal_fstring_route(self, suffix):
        return await self._request(url=f"/integration/hidden-product/{suffix}")
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (tmp_path / "lotus_core_private_only_client.py").write_text(
        """
class FakeCoreClient:
    async def _get_internal_route(self, path):
        return await self._request(url=build_route(path))
""".strip()
        + "\n",
        encoding="utf-8",
    )

    implemented = _implemented_core_domain_product_reads(tmp_path)
    expected_internal_routes = (
        ("lotus_core_private_helper_client.py", "_get_internal_route"),
        ("lotus_core_private_helper_client.py", "_get_mixed_internal_route"),
        ("lotus_core_private_helper_client.py", "_get_fstring_internal_route"),
        ("lotus_core_private_helper_client.py", "_get_bare_path_route"),
        ("lotus_core_private_helper_client.py", "_get_format_internal_route"),
        (
            "lotus_core_private_helper_client.py",
            "_get_resolved_opaque_fstring_route",
        ),
        ("lotus_core_private_helper_client.py", "_get_default_quote_route"),
        ("lotus_core_private_helper_client.py", "_get_shadowed_quote_route"),
        ("lotus_core_private_helper_client.py", "_get_assigned_internal_route"),
        ("lotus_core_private_helper_client.py", "_get_reassigned_alias_route"),
        ("lotus_core_private_helper_client.py", "_get_attribute_route"),
        ("lotus_core_private_helper_client.py", "_get_namespace_attribute_route"),
        ("lotus_core_private_helper_client.py", "_get_literal_route"),
        ("lotus_core_private_helper_client.py", "_get_split_literal_route"),
        ("lotus_core_private_helper_client.py", "_get_namespace_boundary_route"),
        ("lotus_core_private_only_client.py", "_get_internal_route"),
    )
    for client_module, client_method in expected_internal_routes:
        assert (
            client_module,
            client_method,
            _UNRESOLVED_ROUTE_TEMPLATE,
        ) in implemented
    assert (
        "lotus_core_private_helper_client.py",
        "_get_literal_fstring_route",
        "/integration/hidden-product/{}",
    ) in implemented
    assert (
        "lotus_core_private_helper_client.py",
        "_get_safe_quote_route",
        _UNRESOLVED_ROUTE_TEMPLATE,
    ) not in implemented

    with pytest.raises(AssertionError) as exc_info:
        _assert_implemented_core_reads_are_declared(tmp_path)

    message = str(exc_info.value)
    assert (
        f"lotus_core_private_helper_client.py:_get_internal_route [{_UNRESOLVED_ROUTE_TEMPLATE}]"
    ) in message
    for caller_parameter_helper in (
        "_get_parameter_route",
        "_get_parameter_alias",
        "_get_parameter_concat",
        "_get_parameter_fstring",
        "_get_parameter_varargs",
    ):
        assert caller_parameter_helper in message


@pytest.mark.parametrize(
    "source",
    (
        """
def quote(value, safe=""):
    return value

class FakeCoreClient:
    async def _get_local_quote_route(self, path):
        return await self._request(url=f"{quote(path, safe='')}/suffix")
""",
        """
from local_helpers import quote

class FakeCoreClient:
    async def _get_external_quote_route(self, path):
        return await self._request(url=f"{quote(path, safe='')}/suffix")
""",
        """
from urllib.parse import quote

def passthrough(value, safe=""):
    return value

quote = passthrough

class FakeCoreClient:
    async def _get_rebound_quote_route(self, path):
        return await self._request(url=f"{quote(path, safe='')}/suffix")
""",
        """
from urllib.parse import quote as q

class FakeCoreClient:
    async def _get_aliased_quote_route(self, path):
        return await self._request(url=f"{q(path, safe='')}/suffix")
""",
    ),
)
def test_quote_route_interpolation_requires_trusted_provenance(
    tmp_path: Path,
    source: str,
) -> None:
    client_path = tmp_path / "lotus_core_quote_provenance_client.py"
    client_path.write_text(source.strip() + "\n", encoding="utf-8")

    implemented = _implemented_core_domain_product_reads(tmp_path)

    assert any(
        module == client_path.name
        and method.startswith("_get_")
        and route == _UNRESOLVED_ROUTE_TEMPLATE
        for module, method, route in implemented
    )


def test_unresolved_routes_require_named_generic_transport_allowlist(tmp_path: Path) -> None:
    (tmp_path / "lotus_core_query_client.py").write_text(
        """
from urllib.parse import quote

class FakeCoreClient:
    async def _get_query_resource(self, path):
        return await self._request(url=f"{self._query_base_url}{path}")

    async def _unlisted_transport(self, path):
        return await self._request(url=path)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    implemented = _implemented_core_domain_product_reads(tmp_path)

    assert (
        "lotus_core_query_client.py",
        "_get_query_resource",
        _UNRESOLVED_ROUTE_TEMPLATE,
    ) not in implemented
    assert (
        "lotus_core_query_client.py",
        "_unlisted_transport",
        _UNRESOLVED_ROUTE_TEMPLATE,
    ) in implemented


def test_named_transport_allowlist_rejects_internal_route_expression(tmp_path: Path) -> None:
    (tmp_path / "lotus_core_query_client.py").write_text(
        """
class FakeCoreClient:
    async def _get_query_resource(self, path):
        return await self._request(url=build_internal_route(path))
""".strip()
        + "\n",
        encoding="utf-8",
    )

    implemented = _implemented_core_domain_product_reads(tmp_path)

    assert (
        "lotus_core_query_client.py",
        "_get_query_resource",
        _UNRESOLVED_ROUTE_TEMPLATE,
    ) in implemented


def test_uncovered_core_client_module_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "lotus_core_uncovered_client.py").write_text(
        """
class FakeCoreClient:
    async def get_unresolved_product_read(self, route_builder):
        return await self._request(url=route_builder())
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as exc_info:
        _assert_implemented_core_reads_are_declared(tmp_path)

    assert "lotus_core_uncovered_client.py" in str(exc_info.value)


def test_declared_core_method_with_extra_integration_read_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "lotus_core_query_client.py").write_text(
        """
class FakeCoreClient:
    async def get_benchmark_catalog(self):
        await self._post_control_plane_resource(
            path="/integration/benchmarks/catalog",
        )
        return await self._post_control_plane_resource(
            path="/integration/benchmarks/undeclared-alias",
        )
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as exc_info:
        _assert_implemented_core_reads_are_declared(tmp_path)

    message = str(exc_info.value)
    assert (
        "lotus_core_query_client.py:get_benchmark_catalog "
        "[/integration/benchmarks/undeclared-alias]"
    ) in message
