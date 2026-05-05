from fastapi import APIRouter, Path, Query

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.config import settings
from app.contracts.dpm_command_center import (
    DpmOutcomeReviewForwardRequest,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
    DpmOutcomeReviewRefreshRequest,
)
from app.middleware.correlation import correlation_id_var
from app.services.dpm_command_center_service import DpmCommandCenterService

router = APIRouter(prefix="/api/v1/dpm/command-center", tags=["DPM Command Center"])


def _dpm_command_center_service() -> DpmCommandCenterService:
    return DpmCommandCenterService(
        dpm_client=DpmClient(
            base_url=settings.management_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        lotus_ai_client=LotusAiClient(
            base_url=settings.ai_service_base_url,
            timeout_seconds=settings.ai_service_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
    )


@router.post(
    "/outcome-reviews/preview",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Preview outcome review",
    description=(
        "What: previews a post-trade expected-versus-realized outcome review through the "
        "lotus-manage RFC-0042 authority. When: call this before creating a persisted review "
        "to confirm source readiness, supportability, lineage, and expected review contents. "
        "How: Gateway forwards the request unchanged to manage and returns a BFF envelope with "
        "manage-published supportability; Gateway does not calculate outcome dimensions."
    ),
)
async def preview_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().preview_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Create outcome review",
    description=(
        "What: creates a persisted post-trade outcome review in lotus-manage. When: call this "
        "after execution evidence is available and a DPM or operations workflow needs an "
        "immutable review object. How: Gateway forwards the create payload unchanged and "
        "preserves manage-owned identifiers, state, hashes, lineage, and supportability."
    ),
)
async def create_outcome_review(
    request: DpmOutcomeReviewForwardRequest,
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().create_outcome_review(
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="List outcome reviews",
    description=(
        "What: lists manage-owned RFC-0042 outcome reviews for command-center triage. When: "
        "call this to populate DPM review queues by portfolio, run, wave, state, and source "
        "freshness posture. How: Gateway passes filters to manage and returns the authoritative "
        "list payload with a normalized supportability summary."
    ),
)
async def list_outcome_reviews(
    portfolio_id: str | None = Query(
        default=None,
        description="Optional portfolio identifier filter for the outcome-review queue.",
        examples=["PB_SG_GLOBAL_BAL_001"],
    ),
    rebalance_run_id: str | None = Query(
        default=None,
        description="Optional rebalance-run identifier filter.",
        examples=["rr_20260415_001"],
    ),
    wave_id: str | None = Query(
        default=None,
        description="Optional rebalance-wave identifier filter.",
        examples=["wave_20260415_sg_balanced"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional manage-published outcome-review state filter.",
        examples=["READY"],
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
        description="Maximum number of outcome-review records to return.",
        examples=[25],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by manage.",
        examples=["or_cursor_0025"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    filters = {
        "portfolio_id": portfolio_id,
        "rebalance_run_id": rebalance_run_id,
        "wave_id": wave_id,
        "state": state,
        "limit": limit,
        "cursor": cursor,
    }
    return await _dpm_command_center_service().list_outcome_reviews(
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review",
    description=(
        "What: returns one authoritative manage outcome review. When: call this for DPM "
        "detail, evidence inspection, and downstream report or AI handoff readiness checks. "
        "How: Gateway retrieves the manage review by id and preserves the manage payload "
        "without recalculating expected or realized outcomes."
    ),
)
async def get_outcome_review(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_outcome_review(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews/{outcome_review_id}/refresh-sources",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Refresh outcome review sources",
    description=(
        "What: asks manage to refresh source evidence for one outcome review. When: call this "
        "after late fills, corrected valuations, or stale source diagnostics require a managed "
        "refresh. How: Gateway forwards refresh controls unchanged and returns manage's updated "
        "supportability and outcome-review state."
    ),
)
async def refresh_outcome_review_sources(
    request: DpmOutcomeReviewRefreshRequest,
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier to refresh.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().refresh_outcome_review_sources(
        outcome_review_id=outcome_review_id,
        body=request.body,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}/supportability",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review supportability",
    description=(
        "What: returns manage-published supportability for one outcome review. When: call this "
        "to decide whether Workbench should enable report generation, AI evidence handoff, or "
        "source-refresh actions. How: Gateway surfaces manage's state, reason codes, blocked "
        "actions, and remediation owner without replacing manage policy."
    ),
)
async def get_outcome_review_supportability(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_outcome_review_supportability(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}/report-input",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review report input",
    description=(
        "What: returns manage-certified report input for an outcome review. When: call this "
        "only after supportability shows report input is available. How: Gateway passes through "
        "the manage report-input contract for downstream report composition without rendering "
        "or reshaping report content."
    ),
)
async def get_outcome_review_report_input(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_outcome_review_report_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/outcome-reviews/{outcome_review_id}/ai-evidence-input",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get outcome review AI evidence input",
    description=(
        "What: returns manage-certified evidence input for governed AI narrative workflows. "
        "When: call this after supportability shows AI evidence is available and the caller "
        "needs traceable evidence for lotus-ai. How: Gateway preserves manage evidence and "
        "does not generate narrative or infer missing evidence."
    ),
)
async def get_outcome_review_ai_evidence_input(
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_outcome_review_ai_evidence_input(
        outcome_review_id=outcome_review_id,
        correlation_id=correlation_id_var.get(),
    )


@router.post(
    "/outcome-reviews/{outcome_review_id}/ai-narrative",
    response_model=DpmOutcomeReviewNarrativeGatewayResponse,
    summary="Request outcome review AI narrative",
    description=(
        "What: requests a governed lotus-ai outcome-review narrative workflow-pack run from "
        "manage-owned DPM outcome AI evidence. When: call this only after manage supportability "
        "shows AI evidence is available and the user needs review-gated PM/CIO/control support "
        "copy. How: Gateway first reads manage's DpmOutcomeAiEvidenceInput, then executes "
        "lotus-ai outcome_review_narrative.pack@v1 as lotus-gateway; Gateway does not generate "
        "narrative, score PMs, approve trades, contact clients, or invent evidence."
    ),
)
async def request_outcome_review_ai_narrative(
    request: DpmOutcomeReviewNarrativeRequest,
    outcome_review_id: str = Path(
        ...,
        description="Manage-owned outcome-review identifier for the bounded AI evidence handoff.",
        examples=["or_20260415_001"],
    ),
) -> DpmOutcomeReviewNarrativeGatewayResponse:
    return await _dpm_command_center_service().request_outcome_review_ai_narrative(
        outcome_review_id=outcome_review_id,
        request=request,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/runs/{rebalance_run_id}/outcome-review",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="Get run outcome review",
    description=(
        "What: resolves the outcome review linked to one manage rebalance run. When: call this "
        "from run-centric command-center views that need post-trade outcome state. How: Gateway "
        "delegates run lookup to manage and returns the linked RFC-0042 review payload."
    ),
)
async def get_run_outcome_review(
    rebalance_run_id: str = Path(
        ...,
        description="Manage-owned rebalance-run identifier.",
        examples=["rr_20260415_001"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    return await _dpm_command_center_service().get_run_outcome_review(
        rebalance_run_id=rebalance_run_id,
        correlation_id=correlation_id_var.get(),
    )


@router.get(
    "/waves/{wave_id}/outcome-reviews",
    response_model=DpmOutcomeReviewGatewayResponse,
    summary="List wave outcome reviews",
    description=(
        "What: lists outcome reviews linked to one manage rebalance wave. When: call this from "
        "wave-centric DPM command-center views to compare post-trade completion across accounts. "
        "How: Gateway delegates wave lookup to manage and preserves each manage-owned review."
    ),
)
async def list_wave_outcome_reviews(
    wave_id: str = Path(
        ...,
        description="Manage-owned rebalance-wave identifier.",
        examples=["wave_20260415_sg_balanced"],
    ),
    state: str | None = Query(
        default=None,
        description="Optional manage-published outcome-review state filter.",
        examples=["READY"],
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of wave-linked outcome reviews to return.",
        examples=[100],
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor returned by manage.",
        examples=["wave_or_cursor_0100"],
    ),
) -> DpmOutcomeReviewGatewayResponse:
    filters = {"state": state, "limit": limit, "cursor": cursor}
    return await _dpm_command_center_service().list_wave_outcome_reviews(
        wave_id=wave_id,
        filters=filters,
        correlation_id=correlation_id_var.get(),
    )
