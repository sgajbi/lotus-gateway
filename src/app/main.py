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
from app.routers.advisor_cockpit import router as advisor_cockpit_router
from app.routers.advisory_copilot import router as advisory_copilot_router
from app.routers.advisory_policy import router as advisory_policy_router
from app.routers.advisory_workspaces import router as advisory_workspaces_router
from app.routers.analytics_diagnostics import router as analytics_diagnostics_router
from app.routers.archive_documents import router as archive_documents_router
from app.routers.composite_performance import router as composite_performance_router
from app.routers.domain_products import router as domain_products_router
from app.routers.dpm_command_center import router as dpm_command_center_router
from app.routers.dpm_construction import router as dpm_construction_router
from app.routers.dpm_proof_packs import router as dpm_proof_packs_router
from app.routers.dpm_waves import router as dpm_waves_router
from app.routers.foundation import router as foundation_router
from app.routers.intake import router as intake_router
from app.routers.platform import router as platform_router
from app.routers.portfolio import router as portfolio_router
from app.routers.proposals import router as proposals_router
from app.routers.reporting import batches_router as reporting_batches_router
from app.routers.reporting import jobs_router as reporting_jobs_router
from app.routers.reporting import router as reporting_router
from app.routers.reporting import schedules_router as reporting_schedules_router
from app.routers.source_products import router as source_products_router
from app.routers.workbench import router as workbench_router


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
            "name": "advisory-copilot",
            "description": (
                "Gateway-facing governed advisory copilot APIs backed by lotus-advise source "
                "truth. Gateway preserves evidence, action, run, review, guardrail, lineage, and "
                "supportability posture without calling lotus-ai or reconstructing advisory "
                "semantics locally."
            ),
        },
    ],
)
setup_logging()
validate_enterprise_runtime_config()
app.middleware("http")(correlation_middleware)
app.middleware("http")(build_enterprise_audit_middleware("lotus-gateway"))
Instrumentator().instrument(app).expose(app)
app.include_router(advisor_cockpit_router)
app.include_router(advisory_copilot_router)
app.include_router(advisory_workspaces_router)
app.include_router(advisory_policy_router)
app.include_router(proposals_router)
app.include_router(platform_router)
app.include_router(domain_products_router)
app.include_router(source_products_router)
app.include_router(intake_router)
app.include_router(foundation_router)
app.include_router(portfolio_router)
app.include_router(composite_performance_router)
app.include_router(dpm_command_center_router)
app.include_router(dpm_construction_router)
app.include_router(dpm_proof_packs_router)
app.include_router(dpm_waves_router)
app.include_router(workbench_router)
app.include_router(reporting_router)
app.include_router(reporting_jobs_router)
app.include_router(reporting_batches_router)
app.include_router(reporting_schedules_router)
app.include_router(archive_documents_router)
app.include_router(analytics_diagnostics_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
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
