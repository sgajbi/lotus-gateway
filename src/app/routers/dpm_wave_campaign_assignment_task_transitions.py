from fastapi import APIRouter, Path

from app.contracts.dpm_waves import (
    DpmCampaignAssignmentTaskTransitionRequest,
    DpmCampaignWorkflowGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_wave_campaign_assignment_common import (
    UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_wave_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center/waves",
    tags=["DPM Command Center"],
)


async def _transition_campaign_assignment_task(
    *,
    campaign_id: str,
    campaign_version: str,
    task_ref: str,
    request: DpmCampaignAssignmentTaskTransitionRequest,
) -> DpmCampaignWorkflowGatewayResponse:
    return await dpm_wave_service().transition_campaign_assignment_task(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        task_ref=task_ref,
        body=request.body.model_dump(mode="json"),
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/campaign-definitions/{campaign_id}/versions/{campaign_version}/assignment-tasks/{task_ref}/transitions",
    response_model=DpmCampaignWorkflowGatewayResponse,
    summary="Record DPM campaign assignment-task transition",
    description=(
        "What: forwards campaign assignment-task transition evidence to lotus-manage. When: call "
        "only for a Gateway-backed explicit command UX. How: Gateway forwards the body unchanged "
        "and preserves Manage transition evidence, from/to status, source refs, reason codes, "
        "supportability, hashes, and boundaries without calculating task state, SLA, approval, "
        "external workflow, orders, OMS execution, fills, settlement, or client contact."
    ),
    responses=UPSTREAM_CAMPAIGN_ASSIGNMENT_ERROR_RESPONSES,
)
async def transition_campaign_assignment_task(
    request: DpmCampaignAssignmentTaskTransitionRequest,
    campaign_id: str = Path(..., description="Manage-owned campaign definition identifier."),
    campaign_version: str = Path(..., description="Manage-owned campaign definition version."),
    task_ref: str = Path(..., description="Manage-owned campaign assignment task reference."),
) -> DpmCampaignWorkflowGatewayResponse:
    return await _transition_campaign_assignment_task(
        campaign_id=campaign_id,
        campaign_version=campaign_version,
        task_ref=task_ref,
        request=request,
    )
