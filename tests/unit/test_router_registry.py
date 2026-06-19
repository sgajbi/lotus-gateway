import ast
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app.router_groups.advisory import PROPOSAL_ROUTERS
from app.router_groups.dpm import DPM_COMMAND_CENTER_ROUTERS, DPM_WAVE_ROUTERS
from app.router_registry import ROUTER_GROUPS, register_routers

_MAIN_MODULE = Path(__file__).parents[2] / "src" / "app" / "main.py"
_ROUTER_REGISTRY_MODULE = Path(__file__).parents[2] / "src" / "app" / "router_registry.py"


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
