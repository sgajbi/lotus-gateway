from typing import Any

from fastapi import status

from app.contracts.dpm_ai_workflow_execution import DpmAiWorkflowExecution
from app.contracts.dpm_waves import (
    DpmOperationsHandoffSummaryGatewayResponse,
    DpmOperationsHandoffSummaryRequest,
    DpmWaveErrorDetail,
    DpmWaveMemoGatewayResponse,
    DpmWaveMemoRequest,
)
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_ai_workflow_execution import (
    DPM_OPERATIONS_HANDOFF_EXECUTION,
    DPM_WAVE_PM_MEMO_EXECUTION,
    validate_dpm_ai_workflow_execution,
)
from app.services.dpm_wave_ai_payloads import (
    WaveReportInput,
    operations_handoff_summary_request_payload,
    operations_handoff_summary_response,
    operations_handoff_summary_task_payload,
    supportability_from,
    wave_pm_memo_request_payload,
    wave_pm_memo_response,
    wave_pm_memo_task_payload,
    wave_report_source_refs,
)
from app.services.dpm_wave_client_protocols import DpmWaveClient
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import (
    raise_product_safe_service_error,
    raise_product_safe_upstream_error,
)


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
        memo_request = wave_pm_memo_request_payload(request)
        ai_status, ai_payload = await self._execute_wave_pm_memo_workflow(
            wave_id=wave_id,
            correlation_id=correlation_id,
            report_input=report_input,
            memo_request=memo_request,
        )

        return wave_pm_memo_response(
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
    ) -> tuple[int, DpmAiWorkflowExecution]:
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
                payload=wave_pm_memo_task_payload(
                    report_input=report_input,
                    memo_request=memo_request,
                ),
                source_refs=wave_report_source_refs(report_input.payload, wave_id),
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
        return ai_status, validate_dpm_ai_workflow_execution(
            ai_payload,
            upstream_status=ai_status,
            correlation_id=correlation_id,
            expectation=DPM_WAVE_PM_MEMO_EXECUTION,
        )

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
        handoff_summary_request = operations_handoff_summary_request_payload(request)
        ai_status, ai_payload = await self._execute_operations_handoff_summary_workflow(
            wave_id=wave_id,
            correlation_id=correlation_id,
            report_input=report_input,
            handoff_summary_request=handoff_summary_request,
        )

        return operations_handoff_summary_response(
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
    ) -> tuple[int, DpmAiWorkflowExecution]:
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
                payload=operations_handoff_summary_task_payload(
                    report_input=report_input,
                    handoff_summary_request=handoff_summary_request,
                ),
                source_refs=wave_report_source_refs(report_input.payload, wave_id),
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
        return ai_status, validate_dpm_ai_workflow_execution(
            ai_payload,
            upstream_status=ai_status,
            correlation_id=correlation_id,
            expectation=DPM_OPERATIONS_HANDOFF_EXECUTION,
        )

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
            supportability=supportability_from(manage_payload),
        )


def _raise_manage_wave_upstream_error(upstream_status: int, payload: dict[str, Any]) -> None:
    raise_product_safe_upstream_error(
        upstream_status,
        payload,
        error_model=DpmWaveErrorDetail,
        error_code="MANAGE_WAVE_UPSTREAM_ERROR",
        default_detail="lotus-manage rebalance-wave request failed",
    )
