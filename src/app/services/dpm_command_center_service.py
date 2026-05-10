from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.config import settings
from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmCommandCenterSupportability,
    DpmOutcomeReviewErrorDetail,
    DpmOutcomeReviewGatewayResponse,
    DpmOutcomeReviewNarrativeGatewayResponse,
    DpmOutcomeReviewNarrativeRequest,
    DpmOutcomeReviewSupportability,
    DpmPortfolioMemoryGatewayResponse,
    DpmPortfolioMemorySupportability,
)


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
        if self._lotus_ai_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="lotus-ai workflow-pack execution is not configured for Gateway.",
            )

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

        supportability = _supportability_from(manage_payload)
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
        ai_status, ai_payload = await self._lotus_ai_client.execute_workflow_pack(
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
            raise HTTPException(
                status_code=ai_status,
                detail={
                    "source_service": "lotus-ai",
                    "upstream_status": ai_status,
                    "error_code": "AI_OUTCOME_REVIEW_NARRATIVE_UPSTREAM_ERROR",
                    "detail": _safe_upstream_detail(ai_payload),
                },
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

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmOutcomeReviewGatewayResponse:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=upstream_status,
                detail=DpmOutcomeReviewErrorDetail(
                    upstream_status=upstream_status,
                    error_code="MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(upstream_payload),
                ).model_dump(),
            )

        return DpmOutcomeReviewGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            supportability=_supportability_from(upstream_payload),
            data=upstream_payload,
        )

    def _compose_command_center_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=upstream_status,
                detail=DpmOutcomeReviewErrorDetail(
                    upstream_status=upstream_status,
                    error_code="MANAGE_COMMAND_CENTER_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(upstream_payload),
                ).model_dump(),
            )

        return DpmCommandCenterGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            supportability=_command_center_supportability_from(upstream_payload),
            data=upstream_payload,
        )

    def _compose_portfolio_memory_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmPortfolioMemoryGatewayResponse:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=upstream_status,
                detail=DpmOutcomeReviewErrorDetail(
                    upstream_status=upstream_status,
                    error_code="MANAGE_PORTFOLIO_MEMORY_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(upstream_payload),
                ).model_dump(),
            )

        return DpmPortfolioMemoryGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            supportability=_portfolio_memory_supportability_from(upstream_payload),
            data=upstream_payload,
        )


def _supportability_from(payload: dict[str, Any]) -> DpmOutcomeReviewSupportability:
    raw = payload.get("supportability")
    supportability = raw if isinstance(raw, dict) else payload
    reason_codes = _list_of_strings(
        supportability.get("reason_codes")
        or supportability.get("reasonCodes")
        or supportability.get("reasons")
        or []
    )
    blocked_actions = _list_of_strings(
        supportability.get("blocked_actions") or supportability.get("blockedActions") or []
    )
    state = (
        supportability.get("state")
        or supportability.get("supportability_state")
        or supportability.get("supportabilityState")
        or "UNKNOWN"
    )
    remediation_owner = supportability.get("remediation_owner") or supportability.get(
        "remediationOwner"
    )

    return DpmOutcomeReviewSupportability(
        state=str(state),
        reason_codes=reason_codes,
        blocked_actions=blocked_actions,
        remediation_owner=str(remediation_owner) if remediation_owner is not None else None,
    )


def _command_center_supportability_from(payload: dict[str, Any]) -> DpmCommandCenterSupportability:
    raw = payload.get("supportability")
    supportability = raw if isinstance(raw, dict) else {}
    mandate_supportability = _mandate_payload_supportability(payload)
    if mandate_supportability is not None and not supportability:
        return mandate_supportability
    data_completeness_state = supportability.get("data_completeness_state") or supportability.get(
        "dataCompletenessState"
    )
    state = (
        supportability.get("state")
        or supportability.get("supportability_state")
        or supportability.get("supportabilityState")
        or data_completeness_state
        or payload.get("command_center_state")
        or payload.get("state")
        or "UNKNOWN"
    )
    source_run_id = (
        supportability.get("source_run_id")
        or supportability.get("sourceRunId")
        or payload.get("monitoring_run_id")
    )
    remediation_owner = supportability.get("remediation_owner") or supportability.get(
        "remediationOwner"
    )
    partial_reasons = _list_of_strings(
        supportability.get("partial_readiness_reasons")
        or supportability.get("partialReadinessReasons")
        or supportability.get("reason_codes")
        or supportability.get("reasonCodes")
        or []
    )

    return DpmCommandCenterSupportability(
        state=str(state),
        data_completeness_state=(
            str(data_completeness_state) if data_completeness_state is not None else None
        ),
        partial_readiness_reasons=partial_reasons,
        source_run_id=str(source_run_id) if source_run_id is not None else None,
        remediation_owner=str(remediation_owner) if remediation_owner is not None else None,
    )


def _mandate_payload_supportability(
    payload: dict[str, Any],
) -> DpmCommandCenterSupportability | None:
    if "mandate_id" not in payload or "portfolio_id" not in payload:
        return None
    field_gap_codes = _list_of_strings(payload.get("field_gap_codes") or [])
    source_lineage = payload.get("source_lineage")
    has_source_lineage = isinstance(source_lineage, list) and bool(source_lineage)
    state = "PARTIAL" if field_gap_codes else "READY"
    if not has_source_lineage:
        state = "PARTIAL"
        field_gap_codes = [*field_gap_codes, "SOURCE_LINEAGE_NOT_PUBLISHED"]
    return DpmCommandCenterSupportability(
        state=state,
        data_completeness_state=state,
        partial_readiness_reasons=field_gap_codes,
        source_run_id=_safe_optional_str(payload.get("mandate_version")),
        remediation_owner="Portfolio Operations" if field_gap_codes else None,
    )


def _portfolio_memory_supportability_from(
    payload: dict[str, Any],
) -> DpmPortfolioMemorySupportability:
    state = (
        payload.get("supportability_state")
        or payload.get("supportabilityState")
        or payload.get("state")
        or "UNKNOWN"
    )
    event_count = payload.get("event_count") or payload.get("eventCount") or 0
    return DpmPortfolioMemorySupportability(
        state=str(state),
        event_count=_safe_int(event_count),
        event_type_counts=_dict_of_ints(payload.get("event_type_counts")),
        source_systems=_list_of_strings(payload.get("source_systems") or []),
        reason_codes=_list_of_strings(payload.get("reason_codes") or []),
        content_hash=_safe_optional_str(payload.get("content_hash")),
    )


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _dict_of_ints(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    counts: dict[str, int] = {}
    for key, count in value.items():
        counts[str(key)] = _safe_int(count)
    return counts


def _safe_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, str):
        try:
            return max(int(value), 0)
        except ValueError:
            return 0
    return 0


def _safe_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


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
