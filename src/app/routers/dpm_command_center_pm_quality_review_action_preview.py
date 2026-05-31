from fastapi import APIRouter

from app.contracts.dpm_command_center import (
    DpmPmOperatingQualityForwardRequest,
    DpmPmOperatingQualityGatewayResponse,
)
from app.middleware.correlation import correlation_id_var
from app.routers.dpm_command_center_pm_quality_common import (
    UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES,
)
from app.services.dpm_service_provider import dpm_command_center_service

router = APIRouter(
    prefix="/api/v1/dpm/command-center",
    tags=["DPM Command Center"],
    responses=UPSTREAM_PM_OPERATING_QUALITY_ERROR_RESPONSES,
)


async def _preview_pm_operating_quality_review_action(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await dpm_command_center_service().preview_pm_operating_quality_review_action(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/pm-operating-quality/review-actions/preview",
    response_model=DpmPmOperatingQualityGatewayResponse,
    summary="Preview PM operating quality review action",
    description=(
        "What: previews a manage-owned PM operating quality supervisory review action over an "
        "existing score run or fairness analysis. When: use this from governance, model-risk, "
        "evidence-remediation, or supervisory-control views before recording a review-action "
        "ledger row. How: Gateway forwards the payload unchanged and preserves Manage target "
        "content hash, bounded rationale, source refs, reason codes, forbidden uses, and "
        "operating boundaries without recalculating scores, recomputing fairness, ranking PMs, "
        "administering HR/compensation/conduct actions, contacting clients, approving trades, "
        "routing orders, or claiming OMS/execution."
    ),
)
async def preview_pm_operating_quality_review_action(
    request: DpmPmOperatingQualityForwardRequest,
) -> DpmPmOperatingQualityGatewayResponse:
    return await _preview_pm_operating_quality_review_action(request)
