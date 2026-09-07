from fastapi import APIRouter

from app.contracts.dpm_command_center import DpmOutcomeReviewErrorDetail
from app.routers.dpm_openapi import manage_upstream_error_responses

UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES = manage_upstream_error_responses(
    error_model=DpmOutcomeReviewErrorDetail,
    not_found_description="lotus-manage could not find the requested command-center resource.",
    conflict_description="lotus-manage rejected the command-center request as conflicting.",
    invalid_payload_description="lotus-manage rejected the command-center payload as invalid.",
    unavailable_description="lotus-manage command-center authority is unavailable or degraded.",
)


def command_center_router() -> APIRouter:
    """One command-center router construction, not eleven identical copies.

    The command-center surface is split across eleven modules so each route
    keeps its own OpenAPI description, but every one of them mounts under the
    same prefix, tag and upstream-error responses. Repeating that construction
    is how one module ends up on a different `responses` map from its siblings
    and answers a lotus-manage outage in a shape no caller was documented.
    """

    return APIRouter(
        prefix="/api/v1/dpm/command-center",
        tags=["DPM Command Center"],
        responses=UPSTREAM_COMMAND_CENTER_ERROR_RESPONSES,
    )
