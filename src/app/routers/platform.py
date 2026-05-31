from fastapi import APIRouter, Header, Query

from app.contracts.platform_capabilities import PlatformCapabilitiesResponse
from app.middleware.correlation import correlation_id_var
from app.services.platform_capabilities_service_provider import platform_capabilities_service

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


@router.get(
    "/capabilities",
    response_model=PlatformCapabilitiesResponse,
    summary="Get Aggregated Platform Capabilities",
    description=(
        "Aggregates lotus-core, lotus-performance, lotus-risk, lotus-advise, "
        "lotus-manage, and lotus-report integration capabilities into one "
        "lotus-gateway contract for UI feature control, shell bootstrap, and "
        "workflow negotiation. Gateway fans out to upstream capability and policy "
        "sources concurrently, applies a bounded per-source timeout, and returns "
        "partial-failure diagnostics instead of serially blocking the shell while "
        "an optional source is degraded."
    ),
)
async def get_platform_capabilities(
    consumer_system: str = Query(
        "lotus-gateway",
        alias="consumerSystem",
        description=(
            "Gateway consumer identity used when upstream services publish "
            "consumer-shaped capabilities. Use the actual downstream product "
            "identity when a source service varies capability posture by consumer."
        ),
        examples=["lotus-gateway", "lotus-workbench"],
    ),
    tenant_id: str = Query(
        "default",
        alias="tenantId",
        description=(
            "Tenant scope for capability evaluation when an upstream service "
            "supports tenant-aware capability publication. Workbench shell "
            "bootstrap typically uses the governed default tenant unless a "
            "tenant-specific experience contract is in force."
        ),
        examples=["default", "tenant-a"],
    ),
    x_correlation_id: str | None = Header(
        default=None,
        alias="X-Correlation-Id",
        description=(
            "Optional caller-supplied correlation identifier propagated through gateway "
            "capability composition for cross-service diagnostics."
        ),
    ),
) -> PlatformCapabilitiesResponse:
    service = platform_capabilities_service()
    correlation_id = x_correlation_id or correlation_id_var.get() or ""
    return await service.get_platform_capabilities(
        consumer_system=consumer_system,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )
