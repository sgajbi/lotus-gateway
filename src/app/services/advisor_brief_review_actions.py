from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, status

from app.contracts.advisor_brief import (
    AdvisorBriefResponse,
    AdvisorBriefWorkflowPackRunReviewActionRequest,
)
from app.services.advisor_brief_client_protocols import AdvisorBriefAiClient
from app.services.advisor_brief_narrative import safe_advisor_brief_error_detail
from app.services.advisor_brief_workflow_pack import (
    assert_advisor_brief_review_action_allowed,
    resolve_advisor_brief_workflow_pack_run_id,
)


@dataclass(frozen=True)
class AdvisorBriefReviewActionContext:
    brief: AdvisorBriefResponse
    run_id: str


class AdvisorBriefLoader(Protocol):
    async def get_performance_advisor_brief(
        self,
        *,
        portfolio_id: str,
        correlation_id: str,
        period: str,
        chart_frequency: str,
        contribution_dimension: str,
        attribution_dimension: str,
        detail_basis: str,
        benchmark_code: str | None,
        explicit_start_date: str | None = None,
        explicit_end_date: str | None = None,
    ) -> AdvisorBriefResponse: ...


async def load_advisor_brief_review_action_context(
    *,
    advisor_brief_loader: AdvisorBriefLoader,
    portfolio_id: str,
    correlation_id: str,
    period: str,
    chart_frequency: str,
    contribution_dimension: str,
    attribution_dimension: str,
    detail_basis: str,
    benchmark_code: str | None,
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
    explicit_start_date: str | None,
    explicit_end_date: str | None,
) -> AdvisorBriefReviewActionContext:
    brief = await advisor_brief_loader.get_performance_advisor_brief(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        explicit_start_date=explicit_start_date,
        explicit_end_date=explicit_end_date,
    )
    run_id = resolve_advisor_brief_workflow_pack_run_id(ai_audit=brief.ai_audit)
    if run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Advisor brief workflow-pack run posture is unavailable for bounded review actions."
            ),
        )
    assert_advisor_brief_review_action_allowed(
        workflow_pack_run=brief.workflow_pack_run,
        run_id=run_id,
        action_type=request.action_type.value,
    )
    return AdvisorBriefReviewActionContext(brief=brief, run_id=run_id)


async def apply_advisor_brief_review_action(
    *,
    lotus_ai_client: AdvisorBriefAiClient,
    run_id: str,
    correlation_id: str,
    request: AdvisorBriefWorkflowPackRunReviewActionRequest,
) -> None:
    (
        review_status,
        review_payload,
    ) = await lotus_ai_client.apply_workflow_pack_run_review_action(
        run_id=run_id,
        correlation_id=correlation_id,
        request_payload={
            "action_type": request.action_type.value,
            "caller_app": "lotus-gateway",
            "reviewed_by": request.reviewed_by,
            "reason": request.reason,
            "replacement_run_id": request.replacement_run_id,
        },
    )
    if review_status != 200:
        raise HTTPException(
            status_code=review_status,
            detail=safe_advisor_brief_error_detail(review_payload),
        )
