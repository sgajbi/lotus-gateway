from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.lotus_ai_client import LotusAiClient
from app.config import settings
from app.contracts.dpm_waves import (
    DpmWaveErrorDetail,
    DpmWaveGatewayResponse,
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


class DpmWaveService:
    def __init__(self, dpm_client: DpmClient, lotus_ai_client: LotusAiClient | None = None):
        self._dpm_client = dpm_client
        self._lotus_ai_client = lotus_ai_client

    async def preview_wave(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.preview_wave(
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def create_wave(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.create_wave(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def list_waves(
        self,
        filters: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.list_waves(
            params=filters,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_items(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_items(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def source_check_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.source_check_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def simulate_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.simulate_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def select_wave_item(
        self,
        wave_id: str,
        wave_item_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.select_wave_item(
            wave_id=wave_id,
            wave_item_id=wave_item_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def approve_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.approve_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def stage_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.stage_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def handoff_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.handoff_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def cancel_wave(
        self,
        wave_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.cancel_wave(
            wave_id=wave_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_proof_pack_posture(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_proof_pack_posture(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_supportability(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_supportability(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_wave_report_input(
        self,
        wave_id: str,
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_wave_report_input(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def request_wave_pm_memo(
        self,
        wave_id: str,
        request: DpmWaveMemoRequest,
        correlation_id: str,
    ) -> DpmWaveMemoGatewayResponse:
        if self._lotus_ai_client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="lotus-ai workflow-pack execution is not configured for Gateway.",
            )

        manage_status, manage_payload = await self._dpm_client.get_wave_report_input(
            wave_id=wave_id,
            correlation_id=correlation_id,
        )
        if manage_status >= status.HTTP_400_BAD_REQUEST:
            raise self._upstream_error(manage_status, manage_payload)

        supportability = _supportability_from(manage_payload)
        memo_request: dict[str, object] = {
            "requested_outputs": request.requested_outputs,
            "audience": request.audience,
        }
        task_payload = {
            "wave_report_input": manage_payload,
            "memo_request": memo_request,
            "supportability": {
                "source_state": supportability.state,
                "reason_codes": supportability.reason_codes,
                "blocked_actions": _WAVE_PM_MEMO_BLOCKED_ACTIONS,
                "requires_human_review": True,
                "unsupported_claims": _WAVE_PM_MEMO_UNSUPPORTED_CLAIMS,
            },
        }
        ai_status, ai_payload = await self._lotus_ai_client.execute_workflow_pack(
            pack_id="dpm_wave_pm_memo.pack",
            version="v1",
            environment="DEVELOPMENT",
            caller_identity_class="INTERNAL_SERVICE",
            workflow_surface="dpm-wave-ai-evidence",
            task_request={
                "task_id": "explain.v1",
                "input_mode": "STRUCTURED_CONTEXT",
                "caller": {
                    "caller_app": "lotus-gateway",
                    "correlation_id": correlation_id,
                },
                "context": {
                    "summary": (
                        "Generate review-gated DPM wave PM memo from manage-owned report input "
                        f"for {wave_id}."
                    ),
                    "payload": task_payload,
                    "source_refs": _wave_report_source_refs(manage_payload, wave_id),
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
                    "error_code": "AI_WAVE_PM_MEMO_UPSTREAM_ERROR",
                    "detail": _safe_upstream_detail(ai_payload),
                },
            )

        return DpmWaveMemoGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=manage_status,
            ai_upstream_status=ai_status,
            supportability=supportability,
            wave_report_input=manage_payload,
            memo_request=memo_request,
            data=ai_payload,
        )

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise self._upstream_error(upstream_status, upstream_payload)

        return DpmWaveGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            supportability=_supportability_from(upstream_payload),
            data=upstream_payload,
        )

    def _upstream_error(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
    ) -> HTTPException:
        return HTTPException(
            status_code=upstream_status,
            detail=DpmWaveErrorDetail(
                upstream_status=upstream_status,
                error_code="MANAGE_WAVE_UPSTREAM_ERROR",
                detail=_safe_upstream_detail(upstream_payload),
            ).model_dump(),
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


def _safe_upstream_detail(payload: dict[str, Any]) -> str:
    detail = payload.get("detail") or payload.get("message") or payload.get("error")
    if isinstance(detail, dict):
        code = detail.get("code")
        message = detail.get("message")
        if code and message:
            return f"{code}: {message}"
    if isinstance(detail, str):
        return detail
    if detail is not None:
        return str(detail)
    return "lotus-manage rebalance-wave request failed"
