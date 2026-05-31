from fastapi import APIRouter

from app.contracts.advisor_cockpit import (
    AdvisorCockpitEnvelopeResponse,
    AdvisorCockpitHouseViewCohortRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.advisory_service_provider import advisor_cockpit_service

router = APIRouter(prefix="/api/v1/advisor-cockpit", tags=["advisor-cockpit"])


async def _evaluate_advisor_cockpit_house_view_cohort(
    request: AdvisorCockpitHouseViewCohortRequest,
) -> AdvisorCockpitEnvelopeResponse:
    return await advisor_cockpit_service().evaluate_house_view_cohort(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/house-view-cohorts/evaluate",
    response_model=AdvisorCockpitEnvelopeResponse,
    summary="Evaluate Advisor Cockpit House-View Cohort",
    description=(
        "Forwards a source-backed tactical house-view affected-cohort request to lotus-advise so "
        "subsequent advisor cockpit reads can surface DPM-owned `HOUSE_VIEW_IMPACT_REVIEW` "
        "actions. Gateway preserves the Advise cohort product and does not discover candidate "
        "portfolios, infer DPM eligibility, create campaigns, approve trades, or claim OMS "
        "execution."
    ),
)
async def evaluate_advisor_cockpit_house_view_cohort(
    request: AdvisorCockpitHouseViewCohortRequest,
) -> AdvisorCockpitEnvelopeResponse:
    return await _evaluate_advisor_cockpit_house_view_cohort(request)
