from typing import Any

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmCommandCenterSupportability,
    DpmExceptionSummaryGatewayResponse,
    DpmExceptionSummaryRequest,
    DpmOutcomeReviewErrorDetail,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
    DpmPmOperatingQualityGatewayResponse,
    DpmPmOperatingQualitySummaryGatewayResponse,
    DpmPmOperatingQualitySummaryRequest,
    DpmPortfolioMemoryGatewayResponse,
)
from app.services import dpm_command_center_ai_context, dpm_command_center_supportability
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import (
    build_upstream_status_gateway_envelope,
    raise_product_safe_service_error,
    raise_product_safe_upstream_error,
)


class DpmCommandCenterService:
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

    async def request_exception_summary(
        self,
        exception_id: str,
        request: DpmExceptionSummaryRequest,
        correlation_id: str,
    ) -> DpmExceptionSummaryGatewayResponse:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)

        manage_status, manage_payload = await self._dpm_client.list_monitoring_exceptions(
            params={
                "portfolio_id": request.portfolio_id,
                "mandate_id": request.mandate_id,
                "state": request.state,
                "limit": 200,
            },
            correlation_id=correlation_id,
        )
        _raise_manage_command_center_error(
            manage_status,
            manage_payload,
            error_code="MANAGE_EXCEPTION_SUMMARY_UPSTREAM_ERROR",
        )

        exception = dpm_command_center_ai_context.find_exception(manage_payload, exception_id)
        if exception is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "source_service": "lotus-manage",
                    "upstream_status": manage_status,
                    "error_code": "MANAGE_MONITORING_EXCEPTION_NOT_FOUND",
                    "detail": (
                        f"Monitoring exception `{exception_id}` was not returned by lotus-manage."
                    ),
                },
            )

        exception_summary_input = (
            dpm_command_center_ai_context.exception_summary_input_from_exception(exception)
        )
        supportability = DpmCommandCenterSupportability(
            state="READY",
            data_completeness_state="READY",
            partial_readiness_reasons=[],
            source_run_id=dpm_command_center_supportability.safe_optional_str(
                exception.get("monitoring_run_id")
            ),
        )
        summary_request: dict[str, object] = {
            "requested_outputs": request.requested_outputs,
            "audience": request.audience,
        }
        task_payload = dpm_command_center_ai_context.exception_summary_task_payload(
            exception_summary_input=exception_summary_input,
            summary_request=summary_request,
            supportability=supportability,
        )
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="dpm_exception_summary.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-exception-summary-ai-evidence",
            task_request=build_workflow_pack_task_request(
                correlation_id=correlation_id,
                summary=(
                    "Generate review-gated DPM exception summary from manage-owned "
                    f"monitoring exception {exception_id}."
                ),
                payload=task_payload,
                source_refs=dpm_command_center_ai_context.exception_summary_source_refs(
                    exception_summary_input
                ),
            ),
            correlation_id=correlation_id,
        )
        if ai_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_service_error(
                ai_status,
                ai_payload,
                source_service="lotus-ai",
                error_code="AI_EXCEPTION_SUMMARY_UPSTREAM_ERROR",
                default_detail="lotus-ai exception summary request failed",
            )

        return DpmExceptionSummaryGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=manage_status,
            ai_upstream_status=ai_status,
            supportability=supportability,
            exception_summary_input=exception_summary_input,
            exception_summary_request=summary_request,
            data=ai_payload,
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

        manage_status, manage_payload = await self._dpm_client.get_outcome_review_ai_evidence_input(
            outcome_review_id=outcome_review_id,
            correlation_id=correlation_id,
        )
        _raise_manage_command_center_error(
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
        task_payload = dpm_command_center_ai_context.outcome_review_narrative_task_payload(
            ai_evidence_input=manage_payload,
            narrative_request=narrative_request,
            supportability=supportability,
        )
        source_refs = dpm_command_center_ai_context.outcome_ai_source_refs(
            manage_payload, outcome_review_id
        )
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
                payload=task_payload,
                source_refs=source_refs,
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

        return DpmOutcomeReviewNarrativeGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=manage_status,
            ai_upstream_status=ai_status,
            supportability=supportability,
            ai_evidence_input=manage_payload,
            narrative_request=narrative_request,
            data=ai_payload,
        )

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

    async def preview_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_score_run(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_score_run(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_score_run(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_fairness_analysis(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_fairness_analysis(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_fairness_analysis(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_fairness_analyses(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_fairness_analyses(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_fairness_analysis(
        self,
        fairness_analysis_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_fairness_analysis(
            fairness_analysis_id=fairness_analysis_id,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_review_action(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_review_action(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_review_action(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_review_actions(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_review_actions(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_review_action(
        self,
        review_action_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_review_action(
            review_action_id=review_action_id,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def preview_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.preview_pm_operating_quality_summary_invocation(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def create_pm_operating_quality_summary_invocation(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.create_pm_operating_quality_summary_invocation(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_summary_invocations(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_summary_invocations(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_summary_invocation(
        self,
        summary_invocation_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_summary_invocation(
            summary_invocation_id=summary_invocation_id,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_score_runs(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_score_runs(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_score_run(
        self,
        score_run_id: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.get_pm_operating_quality_score_run(
            score_run_id=score_run_id,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def request_pm_operating_quality_summary(
        self,
        score_run_id: str,
        request: DpmPmOperatingQualitySummaryRequest,
        correlation_id: str,
    ) -> DpmPmOperatingQualitySummaryGatewayResponse:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)

        manage_status, manage_payload = await self._dpm_client.get_pm_operating_quality_score_run(
            score_run_id=score_run_id,
            correlation_id=correlation_id,
        )
        _raise_manage_command_center_error(
            manage_status,
            manage_payload,
            error_code="MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR",
        )

        score_run = dpm_command_center_ai_context.pm_quality_score_run_from(manage_payload)
        if score_run is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "source_service": "lotus-manage",
                    "upstream_status": manage_status,
                    "error_code": "MANAGE_PM_OPERATING_QUALITY_SCORE_RUN_MISSING",
                    "detail": (
                        f"Manage response for score run `{score_run_id}` did not include a "
                        "score_run object."
                    ),
                },
            )

        supportability = dpm_command_center_supportability.pm_operating_quality_supportability_from(
            manage_payload
        )
        summary_request: dict[str, object] = {
            "requested_outputs": request.requested_outputs,
            "audience": request.audience,
        }
        task_payload = dpm_command_center_ai_context.pm_quality_summary_task_payload(
            manage_payload=manage_payload,
            score_run=score_run,
            summary_request=summary_request,
            supportability=supportability,
        )

        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="pm_quality_summary.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-pm-quality-ai-evidence",
            task_request=build_workflow_pack_task_request(
                correlation_id=correlation_id,
                summary=(
                    "Generate review-gated PM operating quality summary from "
                    f"Manage-owned score-run evidence for {score_run_id}."
                ),
                payload=task_payload,
                source_refs=dpm_command_center_ai_context.pm_quality_summary_source_refs(score_run),
            ),
            correlation_id=correlation_id,
        )
        if ai_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_service_error(
                ai_status,
                ai_payload,
                source_service="lotus-ai",
                error_code="AI_PM_OPERATING_QUALITY_SUMMARY_UPSTREAM_ERROR",
                default_detail="lotus-ai PM operating quality summary request failed",
            )

        return DpmPmOperatingQualitySummaryGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=manage_status,
            ai_upstream_status=ai_status,
            supportability=supportability,
            score_run=score_run,
            summary_request=summary_request,
            data=ai_payload,
        )

    async def put_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.put_pm_operating_quality_policy(
            policy_id=policy_id,
            policy_version=policy_version,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def list_pm_operating_quality_policies(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.list_pm_operating_quality_policies(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    async def get_pm_operating_quality_policy(
        self,
        policy_id: str,
        policy_version: str,
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_pm_operating_quality_policy(
            policy_id=policy_id,
            policy_version=policy_version,
            correlation_id=correlation_id,
        )
        return self._compose_pm_operating_quality_response(
            upstream_status,
            upstream_payload,
            correlation_id,
        )

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        _raise_manage_command_center_error(
            upstream_status,
            upstream_payload,
            error_code="MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
        )
        return build_upstream_status_gateway_envelope(
            DpmOutcomeReviewGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.outcome_review_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
        )

    def _compose_pm_operating_quality_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmPmOperatingQualityGatewayResponse:
        _raise_manage_command_center_error(
            upstream_status,
            upstream_payload,
            error_code="MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR",
        )
        return build_upstream_status_gateway_envelope(
            DpmPmOperatingQualityGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=(
                dpm_command_center_supportability.pm_operating_quality_supportability_from(
                    upstream_payload
                )
            ),
            upstream_payload=upstream_payload,
        )

    def _compose_command_center_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        _raise_manage_command_center_error(
            upstream_status,
            upstream_payload,
            error_code="MANAGE_COMMAND_CENTER_UPSTREAM_ERROR",
        )
        return build_upstream_status_gateway_envelope(
            DpmCommandCenterGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.command_center_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
        )

    def _compose_portfolio_memory_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmPortfolioMemoryGatewayResponse:
        _raise_manage_command_center_error(
            upstream_status,
            upstream_payload,
            error_code="MANAGE_PORTFOLIO_MEMORY_UPSTREAM_ERROR",
        )
        return build_upstream_status_gateway_envelope(
            DpmPortfolioMemoryGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.portfolio_memory_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
        )


def _raise_manage_command_center_error(
    upstream_status: int,
    payload: dict[str, Any],
    *,
    error_code: str,
) -> None:
    raise_product_safe_upstream_error(
        upstream_status,
        payload,
        error_model=DpmOutcomeReviewErrorDetail,
        error_code=error_code,
        default_detail="lotus-manage command-center request failed",
    )
