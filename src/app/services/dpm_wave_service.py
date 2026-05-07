from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.dpm_waves import (
    DpmWaveErrorDetail,
    DpmWaveGatewayResponse,
    DpmWaveSupportability,
)


class DpmWaveService:
    def __init__(self, dpm_client: DpmClient):
        self._dpm_client = dpm_client

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

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmWaveGatewayResponse:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=upstream_status,
                detail=DpmWaveErrorDetail(
                    upstream_status=upstream_status,
                    error_code="MANAGE_WAVE_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(upstream_payload),
                ).model_dump(),
            )

        return DpmWaveGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            supportability=_supportability_from(upstream_payload),
            data=upstream_payload,
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
