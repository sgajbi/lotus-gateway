import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
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
from app.services import dpm_command_center_supportability
from app.services.lotus_ai_workflow import require_lotus_ai_client
from app.services.upstream_envelope import (
    build_upstream_status_gateway_envelope,
    raise_product_safe_service_error,
    raise_product_safe_upstream_error,
)

_PM_QUALITY_SUMMARY_FORBIDDEN_ACTIONS = [
    "rank_portfolio_managers",
    "make_hr_decisions",
    "make_compensation_decisions",
    "enforce_conduct_action",
    "approve_rebalance",
    "contact_client",
    "place_orders",
    "invent_missing_evidence",
]
_PM_QUALITY_SUMMARY_UNSUPPORTED_CLAIMS = [
    "pm_ranking",
    "hr_decision",
    "compensation_decision",
    "conduct_enforcement",
    "client_message",
    "trade_approval",
    "execution_instruction",
    "oms_acknowledgement",
]


class DpmCommandCenterService:
    def __init__(self, dpm_client: DpmClient, lotus_ai_client: LotusAiClient | None = None):
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
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=manage_status,
                detail=DpmOutcomeReviewErrorDetail(
                    upstream_status=manage_status,
                    error_code="MANAGE_EXCEPTION_SUMMARY_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(manage_payload),
                ).model_dump(),
            )

        exception = _find_exception(manage_payload, exception_id)
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

        exception_summary_input = _exception_summary_input_from_exception(exception)
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
        task_payload = {
            "exception_summary_input": exception_summary_input,
            "exception_summary_request": summary_request,
            "supportability": {
                "source_state": supportability.state,
                "reason_codes": [],
                "blocked_actions": [],
                "forbidden_actions": [
                    "approve_rebalance",
                    "contact_client",
                    "invent_missing_evidence",
                    "override_controls",
                    "place_orders",
                    "score_portfolio_manager",
                ],
                "requires_human_review": True,
                "unsupported_claims": [
                    "trade_approval",
                    "order_instruction",
                    "client_message",
                    "portfolio_manager_scoring",
                ],
            },
        }
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="dpm_exception_summary.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-exception-summary-ai-evidence",
            task_request={
                "task_id": "explain.v1",
                "input_mode": "STRUCTURED_CONTEXT",
                "caller": {
                    "caller_app": "lotus-gateway",
                    "correlation_id": correlation_id,
                },
                "context": {
                    "summary": (
                        "Generate review-gated DPM exception summary from manage-owned "
                        f"monitoring exception {exception_id}."
                    ),
                    "payload": task_payload,
                    "source_refs": _exception_summary_source_refs(exception_summary_input),
                },
                "expected_output_label": "EXPLANATION_ONLY",
            },
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
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=manage_status,
                detail=DpmOutcomeReviewErrorDetail(
                    upstream_status=manage_status,
                    error_code="MANAGE_OUTCOME_REVIEW_AI_EVIDENCE_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(manage_payload),
                ).model_dump(),
            )

        supportability = dpm_command_center_supportability.outcome_review_supportability_from(
            manage_payload
        )
        narrative_request: dict[str, object] = {
            "requested_outputs": request.requested_outputs,
            "audience": request.audience,
        }
        task_payload = {
            "ai_evidence_input": manage_payload,
            "narrative_request": narrative_request,
            "supportability": {
                "source_state": supportability.state,
                "reason_codes": supportability.reason_codes,
                "blocked_actions": supportability.blocked_actions,
                "requires_human_review": True,
                "unsupported_claims": [
                    "client_contact",
                    "trade_approval",
                    "portfolio_manager_scoring",
                ],
            },
        }
        source_refs = _outcome_ai_source_refs(manage_payload, outcome_review_id)
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="outcome_review_narrative.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-outcome-review-ai-evidence",
            task_request={
                "task_id": "explain.v1",
                "input_mode": "STRUCTURED_CONTEXT",
                "caller": {
                    "caller_app": "lotus-gateway",
                    "correlation_id": correlation_id,
                },
                "context": {
                    "summary": (
                        "Generate review-gated outcome-review narrative from bounded "
                        f"AI evidence for {outcome_review_id}."
                    ),
                    "payload": task_payload,
                    "source_refs": source_refs,
                },
                "expected_output_label": "EXPLANATION_ONLY",
            },
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
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=manage_status,
                detail=DpmOutcomeReviewErrorDetail(
                    upstream_status=manage_status,
                    error_code="MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(manage_payload),
                ).model_dump(),
            )

        score_run = _pm_quality_score_run_from(manage_payload)
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
        task_payload: dict[str, object] = {
            "score_run": score_run,
            "summary_request": summary_request,
            "supportability": {
                "source_state": supportability.state,
                "requires_human_review": True,
                "forbidden_actions": _PM_QUALITY_SUMMARY_FORBIDDEN_ACTIONS,
                "unsupported_claims": _PM_QUALITY_SUMMARY_UNSUPPORTED_CLAIMS,
            },
        }
        portfolio_memory_context = manage_payload.get("portfolio_memory_context")
        if isinstance(portfolio_memory_context, dict):
            task_payload["portfolio_memory_context"] = portfolio_memory_context

        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="pm_quality_summary.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-pm-quality-ai-evidence",
            task_request={
                "task_id": "explain.v1",
                "input_mode": "STRUCTURED_CONTEXT",
                "caller": {
                    "caller_app": "lotus-gateway",
                    "correlation_id": correlation_id,
                },
                "context": {
                    "summary": (
                        "Generate review-gated PM operating quality summary from "
                        f"Manage-owned score-run evidence for {score_run_id}."
                    ),
                    "payload": task_payload,
                    "source_refs": _pm_quality_summary_source_refs(score_run),
                },
                "expected_output_label": "EXPLANATION_ONLY",
            },
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


def _pm_quality_score_run_from(payload: dict[str, Any]) -> dict[str, object] | None:
    score_run = payload.get("score_run")
    if isinstance(score_run, dict):
        return score_run
    if payload.get("score_run_id") is not None:
        return payload
    return None


def _pm_quality_summary_source_refs(score_run: dict[str, object]) -> list[str]:
    refs: list[str] = []
    source_refs = score_run.get("source_refs")
    if isinstance(source_refs, list):
        for item in source_refs:
            ref = _source_ref_label(item)
            if ref is not None:
                refs.append(ref)

    score_run_id = dpm_command_center_supportability.safe_optional_str(
        score_run.get("score_run_id")
    )
    if score_run_id is not None:
        refs.append(f"lotus-manage:pm-quality-score-run:{score_run_id}")
    policy_id = dpm_command_center_supportability.safe_optional_str(score_run.get("policy_id"))
    policy_version = dpm_command_center_supportability.safe_optional_str(
        score_run.get("policy_version")
    )
    if policy_id is not None and policy_version is not None:
        refs.append(f"lotus-manage:pm-quality-policy:{policy_id}:{policy_version}")

    return sorted(set(refs))


def _source_ref_label(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None
    source_system = value.get("source_system") or value.get("sourceSystem") or "lotus-manage"
    source_type = value.get("source_type") or value.get("sourceType") or value.get("product_name")
    source_id = value.get("source_id") or value.get("sourceId")
    if source_type is None or source_id is None:
        return None
    return f"{source_system}:{source_type}:{source_id}"


def _find_exception(payload: dict[str, Any], exception_id: str) -> dict[str, Any] | None:
    items = payload.get("items")
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("exception_id") == exception_id:
            return item
    return None


def _exception_summary_input_from_exception(exception: dict[str, Any]) -> dict[str, object]:
    exception_id = str(exception.get("exception_id") or "")
    portfolio_id = str(exception.get("portfolio_id") or "")
    content_hash = _content_hash(
        {
            "exception_id": exception_id,
            "portfolio_id": portfolio_id,
            "state": exception.get("state"),
            "severity": exception.get("severity"),
            "reason_code": exception.get("reason_code"),
            "recommended_action": exception.get("recommended_action"),
            "source_lineage": exception.get("source_lineage"),
        }
    )
    source_refs = _bounded_exception_source_refs(exception, content_hash)
    bounded_exception = {
        "exception_id": exception_id,
        "portfolio_id": portfolio_id,
        "mandate_id": dpm_command_center_supportability.safe_optional_str(
            exception.get("mandate_id")
        )
        or "",
        "severity": str(exception.get("severity") or "UNKNOWN"),
        "state": str(exception.get("state") or "UNKNOWN"),
        "reason_code": str(exception.get("reason_code") or "UNKNOWN"),
        "recommended_action": str(exception.get("recommended_action") or "REVIEW_WITH_PM"),
        "detected_at": dpm_command_center_supportability.safe_optional_str(
            exception.get("detected_at")
        )
        or "",
        "source_refs": source_refs,
    }
    evidence_ref = {
        "source_system": "lotus-manage",
        "source_type": "DPM_EXCEPTION_SUMMARY_INPUT",
        "source_id": f"{portfolio_id}:dpm_exception_summary_input:{exception_id}",
        "content_hash": content_hash,
    }
    return {
        "contract_version": "1.0",
        "portfolio_id": portfolio_id,
        "mandate_id": bounded_exception["mandate_id"],
        "as_of_date": dpm_command_center_supportability.safe_optional_str(
            exception.get("as_of_date")
        )
        or "",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "exception_count": 1,
        "exceptions": [bounded_exception],
        "source_refs": [evidence_ref],
        "redaction_policy": "NO_RAW_PAYLOADS",
        "evidence_ref": evidence_ref,
        "content_hash": content_hash,
    }


def _bounded_exception_source_refs(
    exception: dict[str, Any],
    content_hash: str,
) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = [
        {
            "source_system": "lotus-manage",
            "source_type": "DPM_MONITORING_EXCEPTION",
            "source_id": str(exception.get("exception_id") or ""),
            "content_hash": content_hash,
        }
    ]
    source_lineage = exception.get("source_lineage")
    if isinstance(source_lineage, list):
        for index, item in enumerate(source_lineage):
            if isinstance(item, dict):
                source_system = item.get("source_system") or item.get("sourceSystem")
                source_type = item.get("source_type") or item.get("product_name")
                source_id = item.get("source_id") or item.get("product_version") or index
                if source_system and source_type:
                    refs.append(
                        {
                            "source_system": str(source_system),
                            "source_type": str(source_type),
                            "source_id": str(source_id),
                            "content_hash": dpm_command_center_supportability.safe_optional_str(
                                item.get("content_hash")
                            )
                            or content_hash,
                        }
                    )
    return refs


def _exception_summary_source_refs(exception_summary_input: dict[str, object]) -> list[str]:
    refs = [f"lotus-manage:exception-summary:{exception_summary_input['content_hash']}"]
    exceptions = exception_summary_input.get("exceptions")
    if isinstance(exceptions, list):
        for item in exceptions:
            if isinstance(item, dict):
                exception_id = item.get("exception_id")
                if exception_id:
                    refs.append(f"lotus-manage:monitoring-exception:{exception_id}")
    return sorted(set(refs))


def _content_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _outcome_ai_source_refs(payload: dict[str, Any], outcome_review_id: str) -> list[str]:
    source_refs: list[str] = [f"lotus-manage:outcome-review:{outcome_review_id}"]
    evidence_ref = payload.get("evidence_ref")
    if isinstance(evidence_ref, dict):
        source_id = evidence_ref.get("source_id")
        if source_id is not None:
            source_refs.append(f"lotus-manage:outcome-ai-evidence:{source_id}")
    if len(source_refs) == 1:
        source_refs.append(f"lotus-manage:outcome-ai-evidence:{outcome_review_id}")
    return source_refs


def _safe_upstream_detail(payload: dict[str, Any]) -> str:
    detail = payload.get("detail") or payload.get("message") or payload.get("error")
    if isinstance(detail, str):
        return detail
    if detail is not None:
        return str(detail)
    return "lotus-manage outcome-review request failed"
