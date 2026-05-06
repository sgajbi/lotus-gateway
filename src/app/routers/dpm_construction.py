from typing import Any

from fastapi import APIRouter, Path

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.dpm_construction import (
    DpmConstructionErrorDetail,
    DpmConstructionGatewayResponse,
    DpmConstructionGenerateRequest,
    DpmConstructionSelectionRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.dpm_construction_service import DpmConstructionService

router = APIRouter(
    prefix="/api/v1/dpm/command-center/construction",
    tags=["DPM Command Center"],
)
_UPSTREAM_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    409: {
        "model": DpmConstructionErrorDetail,
        "description": "lotus-manage rejected the construction request.",
    },
    422: {
        "model": DpmConstructionErrorDetail,
        "description": "lotus-manage rejected the construction payload as invalid.",
    },
    503: {
        "model": DpmConstructionErrorDetail,
        "description": "lotus-manage construction authority is unavailable or degraded.",
    },
}


def _dpm_construction_service() -> DpmConstructionService:
    return DpmConstructionService(
        dpm_client=DpmClient(
            base_url=settings.management_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


@router.post(
    "/alternative-sets/generate",
    response_model=DpmConstructionGatewayResponse,
    summary="Generate construction alternatives",
    description=(
        "What: asks lotus-manage to generate an RFC-0039 construction alternative set for "
        "Workbench comparison. When: call this after source readiness and mandate context are "
        "available and a PM needs construction choices before approval. How: Gateway forwards "
        "the payload and idempotency key to manage, then preserves the manage alternative set "
        "without optimizing, recomputing metrics, or selecting an alternative."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def generate_construction_alternative_set(
    request: DpmConstructionGenerateRequest,
) -> DpmConstructionGatewayResponse:
    return await _dpm_construction_service().generate_alternative_set(
        body=request.body,
        idempotency_key=request.idempotency_key,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/alternative-sets/{alternative_set_id}",
    response_model=DpmConstructionGatewayResponse,
    summary="Get construction alternative set",
    description=(
        "What: returns one manage-owned RFC-0039 construction alternative set. When: call this "
        "to reopen comparison, audit selected posture, or populate Workbench detail views. "
        "How: Gateway retrieves the manage payload by id and preserves alternative ids, method "
        "statuses, objective traces, constraint traces, comparison metrics, diagnostics, and "
        "lineage without recalculation."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def get_construction_alternative_set(
    alternative_set_id: str = Path(
        ...,
        description="Manage-owned construction alternative-set identifier.",
        examples=["cas_001"],
    ),
) -> DpmConstructionGatewayResponse:
    return await _dpm_construction_service().get_alternative_set(
        alternative_set_id=alternative_set_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/alternative-sets/{alternative_set_id}/selections",
    response_model=DpmConstructionGatewayResponse,
    summary="Select construction alternative",
    description=(
        "What: records a PM or workflow selection against a manage-owned construction "
        "alternative set. When: call this only after the user chooses a visible alternative and "
        "supportability allows selection. How: Gateway forwards the selection payload to manage "
        "and preserves the returned audit decision; it does not execute trades or choose for the "
        "user."
    ),
    responses=_UPSTREAM_ERROR_RESPONSES,
)
async def select_construction_alternative(
    request: DpmConstructionSelectionRequest,
    alternative_set_id: str = Path(
        ...,
        description="Manage-owned construction alternative-set identifier.",
        examples=["cas_001"],
    ),
) -> DpmConstructionGatewayResponse:
    return await _dpm_construction_service().select_alternative(
        alternative_set_id=alternative_set_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )
