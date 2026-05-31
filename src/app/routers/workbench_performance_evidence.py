from fastapi import APIRouter, Path, Response

from app.middleware.correlation import correlation_id_var
from app.services.workbench_service_provider import performance_workspace_service

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@router.get(
    "/{portfolio_id}/performance/evidence/artifacts/{calculation_id}/{artifact_name}",
    summary="Download Performance Evidence Artifact",
    description=(
        "Downloads a performance lineage artifact through the gateway boundary. "
        "Artifact links published in `evidence_view.calculations[].artifacts[]` resolve through "
        "this route, and gateway preserves the upstream content type when the download succeeds. "
        "Workbench and other downstream clients should use this route instead of calling "
        "lotus-performance directly."
    ),
)
async def get_performance_evidence_artifact(
    portfolio_id: str = Path(
        ...,
        description="Canonical portfolio identifier used to scope the evidence artifact download.",
        examples=["PF_1001"],
    ),
    calculation_id: str = Path(
        ...,
        description="Gateway-visible calculation identifier for the requested evidence artifact.",
        examples=["calc-workspace-summary"],
    ),
    artifact_name: str = Path(
        ...,
        description="Artifact filename published for the selected calculation.",
        examples=["request.json"],
    ),
) -> Response:
    _ = portfolio_id
    service = performance_workspace_service()
    correlation_id = correlation_id_var.get()
    content, content_type = await service.get_performance_evidence_artifact(
        calculation_id=calculation_id,
        artifact_name=artifact_name,
        correlation_id=correlation_id,
    )
    return Response(content=content, media_type=content_type or "application/octet-stream")
