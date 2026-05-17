from typing import Any

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.config import settings
from app.contracts.dpm_construction import (
    DpmConstructionErrorDetail,
    DpmConstructionGatewayResponse,
    DpmConstructionSupportability,
)


class DpmConstructionService:
    def __init__(self, dpm_client: DpmClient):
        self._dpm_client = dpm_client

    async def generate_alternative_set(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> DpmConstructionGatewayResponse:
        (
            upstream_status,
            upstream_payload,
        ) = await self._dpm_client.generate_construction_alternative_set(
            body=body,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def get_alternative_set(
        self,
        alternative_set_id: str,
        correlation_id: str,
    ) -> DpmConstructionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.get_construction_alternative_set(
            alternative_set_id=alternative_set_id,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    async def select_alternative(
        self,
        alternative_set_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> DpmConstructionGatewayResponse:
        upstream_status, upstream_payload = await self._dpm_client.select_construction_alternative(
            alternative_set_id=alternative_set_id,
            body=body,
            correlation_id=correlation_id,
        )
        return self._compose_response(upstream_status, upstream_payload, correlation_id)

    def _compose_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmConstructionGatewayResponse:
        if upstream_status >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=upstream_status,
                detail=DpmConstructionErrorDetail(
                    upstream_status=upstream_status,
                    error_code="MANAGE_CONSTRUCTION_UPSTREAM_ERROR",
                    detail=_safe_upstream_detail(upstream_payload),
                ).model_dump(),
            )

        return DpmConstructionGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            upstream_status=upstream_status,
            supportability=_supportability_from(upstream_payload),
            data=upstream_payload,
        )


def _supportability_from(payload: dict[str, Any]) -> DpmConstructionSupportability:
    reason_codes = _reason_codes_from_payload(payload)
    state = payload.get("status") or payload.get("state") or "UNKNOWN"
    selected_alternative_id = payload.get("alternative_id")
    return DpmConstructionSupportability(
        state=str(state),
        reason_codes=sorted(set(reason_codes)),
        selected_alternative_id=(
            str(selected_alternative_id) if selected_alternative_id is not None else None
        ),
    )


def _reason_codes_from_payload(payload: dict[str, Any]) -> list[str]:
    reason_codes = _list_of_strings(payload.get("reason_codes") or payload.get("reasonCodes") or [])
    alternatives = payload.get("alternatives")
    if isinstance(alternatives, list):
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                continue
            diagnostics = alternative.get("diagnostics")
            if not isinstance(diagnostics, dict):
                continue
            enrichment_summary = diagnostics.get("enrichment_summary")
            if isinstance(enrichment_summary, dict):
                reason_codes.extend(
                    _list_of_strings(
                        enrichment_summary.get("reason_codes")
                        or enrichment_summary.get("reasonCodes")
                        or []
                    )
                )
            method_plan = diagnostics.get("method_plan")
            if isinstance(method_plan, dict):
                reason_codes.extend(
                    _list_of_strings(
                        method_plan.get("reason_codes") or method_plan.get("reasonCodes") or []
                    )
                )
            authority_context = diagnostics.get("authority_context")
            if isinstance(authority_context, dict):
                currency_overlay_context = authority_context.get("currency_overlay_context")
                if isinstance(currency_overlay_context, dict):
                    reason_codes.extend(
                        _list_of_strings(
                            currency_overlay_context.get("reason_codes")
                            or currency_overlay_context.get("reasonCodes")
                            or []
                        )
                    )
                execution_acknowledgement_context = authority_context.get(
                    "execution_acknowledgement_context"
                )
                if isinstance(execution_acknowledgement_context, dict):
                    reason_codes.extend(
                        _list_of_strings(
                            execution_acknowledgement_context.get("reason_codes")
                            or execution_acknowledgement_context.get("reasonCodes")
                            or []
                        )
                    )
    return reason_codes


def _list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _safe_upstream_detail(payload: dict[str, Any]) -> str:
    detail = payload.get("detail") or payload.get("message") or payload.get("error")
    if isinstance(detail, str):
        return detail
    if detail is not None:
        return str(detail)
    return "lotus-manage construction request failed"
