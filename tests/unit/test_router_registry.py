import ast
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app.router_groups.advisory import PROPOSAL_ROUTERS
from app.router_groups.dpm import (
    DPM_CAMPAIGN_ROUTERS,
    DPM_COMMAND_CENTER_ROUTERS,
    DPM_PROOF_AND_CONSTRUCTION_ROUTERS,
    DPM_WAVE_ROUTERS,
)
from app.router_registry import DPM_ROUTER_GROUPS, ROUTER_GROUPS, register_routers
from app.services.dpm_manage_mutation_authority import bind_dpm_manage_mutation_authority

_MAIN_MODULE = Path(__file__).parents[2] / "src" / "app" / "main.py"
_ROUTER_REGISTRY_MODULE = Path(__file__).parents[2] / "src" / "app" / "router_registry.py"
_DPM_ROUTER_GROUP_MODULE = Path(__file__).parents[2] / "src" / "app" / "router_groups" / "dpm.py"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_router_registry_mounts_representative_gateway_route_families() -> None:
    app = FastAPI()

    register_routers(app)

    routes = {route.path for route in app.routes}
    assert "/api/v1/workbench/{portfolio_id}/overview" in routes
    assert "/api/v1/proposals/simulate" in routes
    assert "/api/v1/dpm/command-center" in routes
    assert "/api/v1/report-batches/{batch_id}" in routes
    assert "/api/v1/documents/{document_id}" in routes
    assert "/api/v1/ideas/review-queues/advisor" in routes
    assert "/api/v1/advisor-book/portfolios" in routes


def test_advisory_router_group_keeps_proposal_routes_together() -> None:
    routes = {
        route.path
        for router in PROPOSAL_ROUTERS
        for route in router.routes
        if hasattr(route, "path")
    }

    assert "/api/v1/proposals/simulate" in routes
    assert "/api/v1/proposals/{proposal_id}/lineage" in routes


def test_dpm_router_groups_keep_command_center_and_wave_routes_together() -> None:
    command_center_routes = {
        route.path
        for router in DPM_COMMAND_CENTER_ROUTERS
        for route in router.routes
        if hasattr(route, "path")
    }
    wave_routes = {
        route.path
        for router in DPM_WAVE_ROUTERS
        for route in router.routes
        if hasattr(route, "path")
    }

    assert "/api/v1/dpm/command-center" in command_center_routes
    assert "/api/v1/dpm/command-center/mandates/{mandate_id}/health" in command_center_routes
    assert "/api/v1/dpm/command-center/waves" in wave_routes
    assert "/api/v1/dpm/command-center/waves/{wave_id}/supportability" in wave_routes


def test_dpm_router_group_facade_keeps_all_route_families_exported() -> None:
    assert DPM_COMMAND_CENTER_ROUTERS
    assert DPM_CAMPAIGN_ROUTERS
    assert DPM_PROOF_AND_CONSTRUCTION_ROUTERS
    assert DPM_WAVE_ROUTERS
    assert DPM_ROUTER_GROUPS == (
        DPM_COMMAND_CENTER_ROUTERS,
        DPM_CAMPAIGN_ROUTERS,
        DPM_PROOF_AND_CONSTRUCTION_ROUTERS,
        DPM_WAVE_ROUTERS,
    )


def test_registered_dpm_routes_share_manage_mutation_authority_dependency() -> None:
    app = FastAPI()
    register_routers(app)

    dpm_routes = [
        route for route in app.routes if getattr(route, "path", "").startswith("/api/v1/dpm/")
    ]
    assert dpm_routes
    for route in dpm_routes:
        dependency_calls = {
            dependency.call for dependency in getattr(route, "dependant").dependencies
        }
        if route.methods & {"POST", "PUT", "PATCH", "DELETE"}:
            assert bind_dpm_manage_mutation_authority in dependency_calls
        else:
            assert bind_dpm_manage_mutation_authority not in dependency_calls


def test_registered_dpm_mutations_publish_caller_audit_headers() -> None:
    app = FastAPI()
    register_routers(app)
    schema = app.openapi()

    mutation_operations = []
    for path, path_item in schema["paths"].items():
        if not path.startswith("/api/v1/dpm/"):
            continue
        for method in ("post", "put", "patch", "delete"):
            if method in path_item:
                mutation_operations.append(path_item[method])

    assert mutation_operations
    for operation in mutation_operations:
        header_names = {
            parameter["name"]
            for parameter in operation.get("parameters", [])
            if parameter["in"] == "header"
        }
        assert {
            "X-Actor-Id",
            "X-Tenant-Id",
            "X-Role",
            "X-Region",
        } <= header_names


def test_dpm_router_group_facade_delegates_concrete_router_imports() -> None:
    dpm_router_imports = [
        module
        for module in _imported_modules(_DPM_ROUTER_GROUP_MODULE)
        if module.startswith("app.routers.dpm_")
    ]

    assert dpm_router_imports == []


def test_router_registry_registers_concrete_routes_for_middleware_introspection() -> None:
    app = FastAPI()

    register_routers(app)

    assert all(hasattr(route, "path") for route in app.routes)


def test_router_registry_groups_are_non_empty_router_groups() -> None:
    assert ROUTER_GROUPS

    for router_group in ROUTER_GROUPS:
        assert router_group
        assert all(isinstance(router, APIRouter) for router in router_group)


def test_router_registry_groups_do_not_duplicate_router_instances() -> None:
    routers = [router for router_group in ROUTER_GROUPS for router in router_group]

    assert len(routers) == len({id(router) for router in routers})


def test_main_delegates_router_imports_to_registry() -> None:
    router_imports = [
        module for module in _imported_modules(_MAIN_MODULE) if module.startswith("app.routers.")
    ]

    assert router_imports == []


def test_router_registry_delegates_dpm_router_imports_to_group_module() -> None:
    dpm_router_imports = [
        module
        for module in _imported_modules(_ROUTER_REGISTRY_MODULE)
        if module.startswith("app.routers.dpm_")
    ]

    assert dpm_router_imports == []
