from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.contracts.errors import ProblemDetails
from app.enterprise_readiness import (
    build_enterprise_audit_middleware,
    validate_enterprise_runtime_config,
)
from app.middleware.correlation import correlation_id_var, correlation_middleware, setup_logging
from app.router_registry import register_routers


@asynccontextmanager
async def _app_lifespan(application: FastAPI):
    application.state.is_draining = False
    yield
    application.state.is_draining = True


app = FastAPI(
    title="Advisor Experience API",
    version="0.1.0",
    lifespan=_app_lifespan,
    openapi_tags=[
        {"name": "Reports", "description": "Gateway-facing reporting data and command APIs."},
        {
            "name": "Report Jobs",
            "description": (
                "Gateway-facing report job operations for status and support diagnostics."
            ),
        },
        {
            "name": "Report Batches",
            "description": (
                "Gateway-facing report batch materialization, status, control, and bounded "
                "operator-run APIs."
            ),
        },
        {
            "name": "Report Batch Schedules",
            "description": "Gateway-facing report batch scheduler inspection and run APIs.",
        },
        {
            "name": "Archived Documents",
            "description": (
                "Gateway-facing archived document metadata and controlled download APIs."
            ),
        },
        {
            "name": "Analytics Diagnostics",
            "description": (
                "Protected operator analytics UI diagnostics lookup with bounded audit posture."
            ),
        },
        {
            "name": "Composite Performance",
            "description": (
                "Gateway-facing composite performance operations backed by lotus-performance "
                "source-owned calculation, inspection, lineage, and evidence contracts."
            ),
        },
        {
            "name": "DPM Command Center",
            "description": (
                "Gateway BFF composition APIs for DPM command-center, construction, proof-pack, "
                "rebalance-wave, and post-trade outcome-review workflows backed by "
                "lotus-manage authority."
            ),
        },
        {
            "name": "Source Products",
            "description": (
                "Gateway source-consumer routes for source-owned products that Workbench may "
                "display as evidence or supportability posture without recalculating source truth."
            ),
        },
        {
            "name": "advisor-cockpit",
            "description": (
                "Gateway-facing advisor cockpit action, snapshot, supportability, and "
                "acknowledgement APIs backed by lotus-advise source truth."
            ),
        },
        {
            "name": "bank-demo-proof",
            "description": (
                "Gateway-facing RFC-0028 bank-demo proof contract APIs backed by lotus-advise "
                "source-owned scenario, supported-claim, and sanitized proof-pack truth."
            ),
        },
        {
            "name": "Operations",
            "description": "Operational health, readiness, and Prometheus metrics endpoints.",
        },
    ],
)
setup_logging()
validate_enterprise_runtime_config()
app.middleware("http")(correlation_middleware)
app.middleware("http")(build_enterprise_audit_middleware("lotus-gateway"))
Instrumentator().instrument(app).expose(
    app,
    tags=["Operations"],
    summary="Prometheus Metrics",
    description=(
        "Exposes Prometheus scrape metrics for gateway request latency, throughput, and "
        "status-code telemetry. This endpoint is operational telemetry only and does not "
        "return portfolio, advisory, or client-domain data."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Metrics rendering failed because the local collector is unavailable.",
        },
    },
)
register_routers(app)


@app.get(
    "/health",
    tags=["Operations"],
    summary="Health",
    description=(
        "Returns a lightweight gateway process health signal for load balancers and "
        "operator diagnostics. This check confirms the application process is responding."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The gateway process could not produce a health response.",
        },
    },
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/health/live",
    tags=["Operations"],
    summary="Health Live",
    description=(
        "Returns the gateway liveness signal used to confirm the application process should "
        "continue receiving runtime supervision."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "The gateway process could not produce a liveness response.",
        },
    },
)
async def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get(
    "/health/ready",
    tags=["Operations"],
    summary="Health Ready",
    description=(
        "Returns readiness for traffic. During graceful drain the endpoint responds with "
        "503 and a draining status so callers can remove the instance from rotation."
    ),
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The gateway is draining and should not receive new traffic.",
        },
    },
)
async def health_ready(response: Response) -> dict[str, str]:
    if bool(getattr(app.state, "is_draining", False)):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "draining"}
    return {"status": "ready"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    problem = ProblemDetails(
        title="Internal Server Error",
        status=500,
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
        correlation_id=correlation_id_var.get() or "",
        error_code="INTERNAL_ERROR",
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/problem+json",
        content=problem.model_dump(),
    )
