from fastapi import FastAPI

from app.router_registry import register_routers


def test_router_registry_mounts_representative_gateway_route_families() -> None:
    app = FastAPI()

    register_routers(app)

    routes = {route.path for route in app.routes}
    assert "/api/v1/workbench/{portfolio_id}/overview" in routes
    assert "/api/v1/proposals/simulate" in routes
    assert "/api/v1/dpm/command-center" in routes
    assert "/api/v1/report-batches/{batch_id}" in routes
    assert "/api/v1/documents/{document_id}" in routes
