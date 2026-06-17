from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.dpm_waves import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
    DpmWaveErrorDetail,
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
    DpmWaveSupportability,
)
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmWaveClient
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import (
    raise_product_safe_service_error,
    raise_product_safe_upstream_error,
)

_WAVE_PM_MEMO_BLOCKED_ACTIONS = [
    "place_orders",
    "approve_rebalance",
    "override_controls",
    "invent_missing_evidence",
    "contact_client",
]
_WAVE_PM_MEMO_UNSUPPORTED_CLAIMS = [
    "client_contact",
    "trade_approval",
    "portfolio_manager_scoring",
    "execution_instruction",
]
_OPERATIONS_HANDOFF_UNSUPPORTED_CLAIMS = [
    "client_contact",
    "trade_approval",
    "portfolio_manager_scoring",
    "execution_instruction",
    "order_routing",
]


@dataclass(frozen=True)
class WaveReportInput:
    upstream_status: int
    payload: dict[str, Any]
    supportability: DpmWaveSupportability


class DpmWaveAiHandoffMixin:
    _dpm_client: DpmWaveClient
    _lotus_ai_client: LotusAiWorkflowClient | None

    async def request_wave_pm_memo(
        self,
        wave_id: str,
        request: DpmWaveMemoRequest,
        correlation_id: str,
    ) -> DpmWaveMemoGatewayResponse:
        report_input = await self._load_wave_report_input(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        memo_request = _wave_pm_memo_request_payload(request)
        ai_status, ai_payload = await self._execute_wave_pm_memo_workflow(
            wave_id=wave_id,
            correlation_id=correlation_id,
            report_input=report_input,
            memo_request=memo_request,
        )

        return _wave_pm_memo_response(
            correlation_id=correlation_id,
            report_input=report_input,
            memo_request=memo_request,
            ai_upstream_status=ai_status,
            data=ai_payload,
        )

    async def _execute_wave_pm_memo_workflow(
        self,
        *,
        wave_id: str,
        correlation_id: str,
        report_input: WaveReportInput,
        memo_request: dict[str, object],
    ) -> tuple[int, dict[str, Any]]:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="dpm_wave_pm_memo.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-wave-ai-evidence",
            task_request=build_workflow_pack_task_request(
                correlation_id=correlation_id,
                summary=(
                    "Generate review-gated DPM wave PM memo from manage-owned report input "
                    f"for {wave_id}."
                ),
                payload=_wave_pm_memo_task_payload(
                    report_input=report_input,
                    memo_request=memo_request,
                ),
                source_refs=_wave_report_source_refs(report_input.payload, wave_id),
            ),
            correlation_id=correlation_id,
        )
        if ai_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_service_error(
                ai_status,
                ai_payload,
                source_service="lotus-ai",
                error_code="AI_WAVE_PM_MEMO_UPSTREAM_ERROR",
                default_detail="lotus-ai wave PM memo request failed",
            )
        return ai_status, ai_payload

    async def request_operations_handoff_summary(
        self,
        wave_id: str,
        request: DpmOperationsHandoffSummaryRequest,
        correlation_id: str,
    ) -> DpmOperationsHandoffSummaryGatewayResponse:
        report_input = await self._load_wave_report_input(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        handoff_summary_request = _operations_handoff_summary_request_payload(request)
        ai_status, ai_payload = await self._execute_operations_handoff_summary_workflow(
            wave_id=wave_id,
            correlation_id=correlation_id,
            report_input=report_input,
            handoff_summary_request=handoff_summary_request,
        )

        return _operations_handoff_summary_response(
            correlation_id=correlation_id,
            report_input=report_input,
            handoff_summary_request=handoff_summary_request,
            ai_upstream_status=ai_status,
            data=ai_payload,
        )

    async def _execute_operations_handoff_summary_workflow(
        self,
        *,
        wave_id: str,
        correlation_id: str,
        report_input: WaveReportInput,
        handoff_summary_request: dict[str, object],
    ) -> tuple[int, dict[str, Any]]:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)
        ai_status, ai_payload = await lotus_ai_client.execute_workflow_pack(
            pack_id="dpm_operations_handoff_summary.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-operations-handoff-ai-evidence",
            task_request=build_workflow_pack_task_request(
                correlation_id=correlation_id,
                summary=(
                    "Generate review-gated DPM operations handoff summary from "
                    f"manage-owned handoff evidence for {wave_id}."
                ),
                payload=_operations_handoff_summary_task_payload(
                    report_input=report_input,
                    handoff_summary_request=handoff_summary_request,
                ),
                source_refs=_wave_report_source_refs(report_input.payload, wave_id),
            ),
            correlation_id=correlation_id,
        )
        if ai_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_service_error(
                ai_status,
                ai_payload,
                source_service="lotus-ai",
                error_code="AI_OPERATIONS_HANDOFF_SUMMARY_UPSTREAM_ERROR",
                default_detail="lotus-ai operations handoff summary request failed",
            )
        return ai_status, ai_payload

    async def _load_wave_report_input(
        self,
        *,
        wave_id: str,
        correlation_id: str,
    ) -> WaveReportInput:
        manage_status, manage_payload = await self._dpm_client.get_wave_report_input(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            _raise_manage_wave_upstream_error(manage_status, manage_payload)
        return WaveReportInput(
            upstream_status=manage_status,
            payload=manage_payload,
            supportability=_supportability_from(manage_payload),
        )


def _supportability_from(payload: dict[str, Any]) -> DpmWaveSupportability:
    wave = _wave_payload(payload)
    supportability = _supportability_payload(payload, wave)
    state = (
        supportability.get("supportability_state")
        or supportability.get("supportabilityState")
        or supportability.get("state")
        or payload.get("supportability_state")
        or wave.get("supportability_state")
        or "UNKNOWN"
    )
    reason_codes = _list_of_strings(
        supportability.get("reason_codes")
        or supportability.get("reasonCodes")
        or supportability.get("blocked_actions")
        or []
    )
    reason = supportability.get("reason") or supportability.get("supportability_reason")
    if reason is not None:
        reason_codes.append(str(reason))
    issues = supportability.get("issues") or payload.get("issues")
    blocked_actions = _list_of_strings(
        supportability.get("blocked_actions") or supportability.get("blockedActions") or []
    )
    remediation_owner = supportability.get("remediation_owner") or supportability.get(
        "remediationOwner"
    )

    return DpmWaveSupportability(
        state=str(state),
        reason_codes=sorted(set(reason_codes)),
        blocked_actions=blocked_actions,
        wave_id=_safe_str(
            supportability.get("wave_id") or payload.get("wave_id") or wave.get("wave_id")
        ),
        wave_state=_safe_str(
            supportability.get("wave_state") or payload.get("wave_state") or wave.get("state")
        ),
        item_count=_safe_int(supportability.get("item_count") or payload.get("item_count")),
        issue_count=len(issues) if isinstance(issues, list) else 0,
        remediation_owner=_safe_str(remediation_owner),
    )


def _wave_payload(payload: dict[str, Any]) -> dict[str, Any]:
    wave = payload.get("wave")
    return wave if isinstance(wave, dict) else payload


def _supportability_payload(
    payload: dict[str, Any],
    wave: dict[str, Any],
) -> dict[str, Any]:
    supportability = payload.get("supportability") or wave.get("supportability")
    return supportability if isinstance(supportability, dict) else payload


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _safe_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _safe_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _wave_report_source_refs(payload: dict[str, Any], wave_id: str) -> list[str]:
    refs = set(_list_of_strings(payload.get("source_refs") or payload.get("sourceRefs") or []))
    report_input_ref = payload.get("report_input_ref") or payload.get("reportInputRef")
    if report_input_ref:
        refs.add(f"lotus-manage:wave-report-input:{_source_ref_token(report_input_ref)}")
    payload_wave_id = payload.get("wave_id") or payload.get("waveId")
    if payload_wave_id:
        refs.add(f"lotus-manage:wave:{payload_wave_id}")
    refs.add(f"lotus-manage:wave-report-input:{wave_id}")
    return sorted(refs)


def _source_ref_token(value: object) -> str:
    token = str(value)
    return token.removeprefix("report-input:")


def _wave_pm_memo_request_payload(request: DpmWaveMemoRequest) -> dict[str, object]:
    return {
        "requested_outputs": request.requested_outputs,
        "audience": request.audience,
    }


def _wave_pm_memo_task_payload(
    *,
    report_input: WaveReportInput,
    memo_request: dict[str, object],
) -> dict[str, object]:
    return {
        "wave_report_input": report_input.payload,
        "memo_request": memo_request,
        "supportability": _wave_pm_memo_supportability_payload(report_input.supportability),
    }


def _wave_pm_memo_response(
    *,
    correlation_id: str,
    report_input: WaveReportInput,
    memo_request: dict[str, object],
    ai_upstream_status: int,
    data: dict[str, Any],
) -> DpmWaveMemoGatewayResponse:
    return DpmWaveMemoGatewayResponse(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        manage_upstream_status=report_input.upstream_status,
        ai_upstream_status=ai_upstream_status,
        supportability=report_input.supportability,
        wave_report_input=report_input.payload,
        memo_request=memo_request,
        data=data,
    )


def _operations_handoff_summary_request_payload(
    request: DpmOperationsHandoffSummaryRequest,
) -> dict[str, object]:
    return {
        "requested_outputs": request.requested_outputs,
        "audience": request.audience,
    }


def _operations_handoff_summary_task_payload(
    *,
    report_input: WaveReportInput,
    handoff_summary_request: dict[str, object],
) -> dict[str, object]:
    return {
        "wave_report_input": report_input.payload,
        "handoff_summary_request": handoff_summary_request,
        "supportability": _operations_handoff_supportability_payload(report_input.supportability),
    }


def _operations_handoff_summary_response(
    *,
    correlation_id: str,
    report_input: WaveReportInput,
    handoff_summary_request: dict[str, object],
    ai_upstream_status: int,
    data: dict[str, Any],
) -> DpmOperationsHandoffSummaryGatewayResponse:
    return DpmOperationsHandoffSummaryGatewayResponse(
        correlation_id=correlation_id,
        contract_version=settings.contract_version,
        manage_upstream_status=report_input.upstream_status,
        ai_upstream_status=ai_upstream_status,
        supportability=report_input.supportability,
        wave_report_input=report_input.payload,
        handoff_summary_request=handoff_summary_request,
        data=data,
    )


def _wave_pm_memo_supportability_payload(
    supportability: DpmWaveSupportability,
) -> dict[str, object]:
    return {
        "source_state": supportability.state,
        "reason_codes": supportability.reason_codes,
        "blocked_actions": _WAVE_PM_MEMO_BLOCKED_ACTIONS,
        "forbidden_actions": _WAVE_PM_MEMO_BLOCKED_ACTIONS,
        "requires_human_review": True,
        "unsupported_claims": _WAVE_PM_MEMO_UNSUPPORTED_CLAIMS,
    }


def _operations_handoff_supportability_payload(
    supportability: DpmWaveSupportability,
) -> dict[str, object]:
    return {
        "source_state": supportability.state,
        "reason_codes": supportability.reason_codes,
        "blocked_actions": _WAVE_PM_MEMO_BLOCKED_ACTIONS,
        "forbidden_actions": _WAVE_PM_MEMO_BLOCKED_ACTIONS,
        "requires_human_review": True,
        "unsupported_claims": _OPERATIONS_HANDOFF_UNSUPPORTED_CLAIMS,
    }


def _raise_manage_wave_upstream_error(upstream_status: int, payload: dict[str, Any]) -> None:
    raise_product_safe_upstream_error(
        upstream_status,
        payload,
        error_model=DpmWaveErrorDetail,
        error_code="MANAGE_WAVE_UPSTREAM_ERROR",
        default_detail="lotus-manage rebalance-wave request failed",
    )
