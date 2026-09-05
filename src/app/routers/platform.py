from fastapi import APIRouter, Header, HTTPException, Query, status

from app.contracts.platform_capabilities import PlatformCapabilitiesResponse
from app.middleware.caller_identity import admit_caller_tenant, release_caller_identity
from app.routers.correlation import resolve_router_correlation_id
from app.services.platform_capabilities_service_provider import platform_capabilities_service

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def _resolve_admitted_tenant(*, query_tenant: str | None, header_tenant: str | None) -> str:
    """One request admits exactly one tenant scope.

    The explicit query selector and the trusted-context header must agree when
    both are presented; sending two different scopes upstream would let a
    header-fencing source answer for one tenant while the aggregate is labeled
    with the other. The governed default applies only when neither is given."""

    query_value = (query_tenant or "").strip()
    header_value = (header_tenant or "").strip()
    if query_value and header_value and query_value != header_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "platform_tenant_scope_ambiguous",
                "message": (
                    "The tenantId query selector and the X-Tenant-Id caller context "
                    "disagree; present one tenant scope."
                ),
            },
        )
    return query_value or header_value or "default"


async def _get_platform_capabilities(
    *,
    consumer_system: str,
    tenant_id: str | None,
    header_tenant: str | None,
    x_correlation_id: str | None,
) -> PlatformCapabilitiesResponse:
    admitted_tenant = _resolve_admitted_tenant(query_tenant=tenant_id, header_tenant=header_tenant)
    # Bind the resolved scope so the ambient tenant fence on every upstream
    # call this composition makes is exactly the admitted tenant.
    token = admit_caller_tenant(admitted_tenant)
    try:
        service = platform_capabilities_service()
        return await service.get_platform_capabilities(
            consumer_system=consumer_system,
            tenant_id=admitted_tenant,
            correlation_id=resolve_router_correlation_id(x_correlation_id),
        )
    finally:
        release_caller_identity(token)


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
    tenant_id: str | None = Query(
        None,
        alias="tenantId",
        description=(
            "Tenant scope for capability evaluation when an upstream service "
            "supports tenant-aware capability publication. Must agree with the "
            "X-Tenant-Id caller context when both are presented; the governed "
            "default tenant applies only when neither is given."
        ),
        examples=["default", "tenant-a"],
    ),
    header_tenant: str | None = Header(
        default=None,
        alias="X-Tenant-Id",
        description="Trusted caller tenant context; must agree with tenantId when both are given.",
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
    return await _get_platform_capabilities(
        consumer_system=consumer_system,
        tenant_id=tenant_id,
        header_tenant=header_tenant,
        x_correlation_id=x_correlation_id,
    )
