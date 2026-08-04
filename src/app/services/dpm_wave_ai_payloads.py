from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution
from app.contracts.dpm_waves import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
    DpmWaveSupportability,
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


def supportability_from(payload: dict[str, Any]) -> DpmWaveSupportability:
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


def wave_report_source_refs(payload: dict[str, Any], wave_id: str) -> list[str]:
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


def wave_pm_memo_request_payload(request: DpmWaveMemoRequest) -> dict[str, object]:
    return {
        "requested_outputs": request.requested_outputs,
        "audience": request.audience,
    }


def wave_pm_memo_task_payload(
    *,
    report_input: WaveReportInput,
    memo_request: dict[str, object],
) -> dict[str, object]:
    return {
        "wave_report_input": report_input.payload,
        "memo_request": memo_request,
        "supportability": wave_pm_memo_supportability_payload(report_input.supportability),
    }


def wave_pm_memo_response(
    *,
    correlation_id: str,
    report_input: WaveReportInput,
    memo_request: dict[str, object],
    ai_upstream_status: int,
    data: DpmAiWorkflowExecution,
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


def operations_handoff_summary_request_payload(
    request: DpmOperationsHandoffSummaryRequest,
) -> dict[str, object]:
    return {
        "requested_outputs": request.requested_outputs,
        "audience": request.audience,
    }


def operations_handoff_summary_task_payload(
    *,
    report_input: WaveReportInput,
    handoff_summary_request: dict[str, object],
) -> dict[str, object]:
    return {
        "wave_report_input": report_input.payload,
        "handoff_summary_request": handoff_summary_request,
        "supportability": operations_handoff_supportability_payload(report_input.supportability),
    }


def operations_handoff_summary_response(
    *,
    correlation_id: str,
    report_input: WaveReportInput,
    handoff_summary_request: dict[str, object],
    ai_upstream_status: int,
    data: DpmAiWorkflowExecution,
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


def wave_pm_memo_supportability_payload(
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


def operations_handoff_supportability_payload(
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
