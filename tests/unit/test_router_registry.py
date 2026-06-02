import ast
from pathlib import Path

from fastapi import APIRouter, FastAPI

from app.router_registry import ROUTER_GROUPS, register_routers

_MAIN_MODULE = Path(__file__).parents[2] / "src" / "app" / "main.py"


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
