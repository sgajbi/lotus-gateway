from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmOutcomeReviewErrorDetail,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
    DpmOutcomeReviewSupportability,
    DpmPortfolioMemoryGatewayResponse,
)
from app.services import dpm_command_center_ai_context, dpm_command_center_supportability
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_command_center_errors import raise_manage_command_center_error
from app.services.dpm_command_center_exception_summary import (
    DpmCommandCenterExceptionSummaryMixin,
)
from app.services.dpm_pm_operating_quality_service import DpmPmOperatingQualityServiceMixin
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import (
    build_product_safe_upstream_status_gateway_envelope,
    raise_product_safe_service_error,
)


@dataclass(frozen=True)
class DpmOutcomeReviewNarrativeContext:
    manage_status: int
    ai_evidence_input: dict[str, Any]
    supportability: DpmOutcomeReviewSupportability
    narrative_request: dict[str, object]
    task_payload: dict[str, object]
    source_refs: list[str]


class DpmCommandCenterService(
    DpmCommandCenterExceptionSummaryMixin,
    DpmPmOperatingQualityServiceMixin,
):
    def __init__(
        self,
        dpm_client: DpmCommandCenterClient,
        lotus_ai_client: LotusAiWorkflowClient | None = None,
    ):
        self._dpm_client = dpm_client
        self._lotus_ai_client = lotus_ai_client

    async def get_command_center(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_command_center(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def run_monitoring_once(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.run_monitoring_once(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_monitoring_runs(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_monitoring_runs(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_monitoring_run(
        self,
        monitoring_run_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_monitoring_run(
            monitoring_run_id=monitoring_run_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_monitoring_exceptions(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_monitoring_exceptions(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def resolve_monitoring_exception(
        self,
        exception_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.resolve_monitoring_exception(
            exception_id=exception_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate_by_portfolio(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate_by_portfolio(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate(
            mandate_id=mandate_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate_health(
        self,
        mandate_id: str,
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate_health(
            mandate_id=mandate_id,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_mandate_diff(
        self,
        mandate_id: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_mandate_diff(
            mandate_id=mandate_id,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_command_center_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_portfolio_memory(
        self,
        portfolio_id: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPortfolioMemoryGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_portfolio_memory(
            portfolio_id=portfolio_id,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_portfolio_memory_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def search_portfolio_memory(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPortfolioMemoryGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.search_portfolio_memory(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_portfolio_memory_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_outcome_review(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.preview_outcome_review(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def create_outcome_review(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.create_outcome_review(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def list_outcome_reviews(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_outcome_reviews(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_outcome_review(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_outcome_review(
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def refresh_outcome_review_sources(
        self,
        outcome_review_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.refresh_outcome_review_sources(
            outcome_review_id=outcome_review_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_outcome_review_supportability(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_outcome_review_supportability(
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_outcome_review_report_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_outcome_review_report_input(
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id: str,
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_outcome_review_ai_evidence_input(
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

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

    async def get_run_outcome_review(
        self,
        rebalance_run_id: str,
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_run_outcome_review(
            rebalance_run_id=rebalance_run_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def list_wave_outcome_reviews(
        self,
        wave_id: str,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_wave_outcome_reviews(
            wave_id=wave_id,
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmOutcomeReviewGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.outcome_review_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
            error_model=DpmOutcomeReviewErrorDetail,
            error_code="MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
            default_detail="lotus-manage command-center request failed",
        )

    def _compose_command_center_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmCommandCenterGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.command_center_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
            error_model=DpmOutcomeReviewErrorDetail,
            error_code="MANAGE_COMMAND_CENTER_UPSTREAM_ERROR",
            default_detail="lotus-manage command-center request failed",
        )

    def _compose_portfolio_memory_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmPortfolioMemoryGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmPortfolioMemoryGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.portfolio_memory_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
            error_model=DpmOutcomeReviewErrorDetail,
            error_code="MANAGE_PORTFOLIO_MEMORY_UPSTREAM_ERROR",
            default_detail="lotus-manage command-center request failed",
        )
