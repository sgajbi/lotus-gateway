from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.dpm_command_center import (
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
    DpmOutcomeReviewSupportability,
)
from app.services import dpm_command_center_ai_context, dpm_command_center_supportability
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_command_center_errors import raise_manage_command_center_error
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import raise_product_safe_service_error


@dataclass(frozen=True)
class DpmOutcomeReviewNarrativeContext:
    manage_status: int
    ai_evidence_input: dict[str, Any]
    supportability: DpmOutcomeReviewSupportability
    narrative_request: dict[str, object]
    task_payload: dict[str, object]
    source_refs: list[str]


class DpmCommandCenterOutcomeNarrativeMixin:
    _dpm_client: DpmCommandCenterClient
    _lotus_ai_client: LotusAiWorkflowClient | None

    async def request_outcome_review_ai_narrative(
        self,
        outcome_review_id: str,
        request: DpmOutcomeReviewNarrativeRequest,
        correlation_id: str,
    ) -> DpmOutcomeReviewNarrativeGatewayResponse:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)

        context = await self._build_outcome_review_narrative_context(
            outcome_review_id=outcome_review_id,
            request=request,
            correlation_id=correlation_id,
        )
        ai_status, ai_payload = await self._execute_outcome_review_narrative_pack(
            lotus_ai_client=lotus_ai_client,
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
            context=context,
        )

        return DpmOutcomeReviewNarrativeGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=context.manage_status,
            ai_upstream_status=ai_status,
            supportability=context.supportability,
            ai_evidence_input=context.ai_evidence_input,
            narrative_request=context.narrative_request,
            data=ai_payload,
        )

    async def _build_outcome_review_narrative_context(
        self,
        *,
        outcome_review_id: str,
        request: DpmOutcomeReviewNarrativeRequest,
        correlation_id: str,
    ) -> DpmOutcomeReviewNarrativeContext:
        manage_status, manage_payload = await self._dpm_client.get_outcome_review_ai_evidence_input(
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
        )
        raise_manage_command_center_error(
            manage_status,
            manage_payload,
            error_code="MANAGE_OUTCOME_REVIEW_AI_EVIDENCE_UPSTREAM_ERROR",
        )
        supportability = dpm_command_center_supportability.outcome_review_supportability_from(
            manage_payload
        )
        narrative_request: dict[str, object] = {
            "requested_outputs": request.requested_outputs,
            "audience": request.audience,
        }
        return DpmOutcomeReviewNarrativeContext(
            manage_status=manage_status,
            ai_evidence_input=manage_payload,
            supportability=supportability,
            narrative_request=narrative_request,
            task_payload=dpm_command_center_ai_context.outcome_review_narrative_task_payload(
                ai_evidence_input=manage_payload,
                narrative_request=narrative_request,
                supportability=supportability,
            ),
            source_refs=dpm_command_center_ai_context.outcome_ai_source_refs(
                manage_payload, outcome_review_id
            ),
        )

    async def _execute_outcome_review_narrative_pack(
        self,
        *,
        lotus_ai_client: LotusAiWorkflowClient,
        outcome_review_id: str,
        correlation_id: str,
        context: DpmOutcomeReviewNarrativeContext,
    ) -> tuple[int, dict[str, Any]]:
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="outcome_review_narrative.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-outcome-review-ai-evidence",
            task_request=build_workflow_pack_task_request(
                correlation_id=correlation_id,
                summary=(
                    "Generate review-gated outcome-review narrative from bounded "
                    f"AI evidence for {outcome_review_id}."
                ),
                payload=context.task_payload,
                source_refs=context.source_refs,
            ),
            correlation_id=correlation_id,
        )
        if ai_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_service_error(
                ai_status,
                ai_payload,
                source_service="lotus-ai",
                error_code="AI_OUTCOME_REVIEW_NARRATIVE_UPSTREAM_ERROR",
                default_detail="lotus-ai outcome-review narrative request failed",
            )
        return ai_status, ai_payload
