from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.dpm_command_center import (
    DpmPmOperatingQualitySummaryGatewayResponse,
    DpmPmOperatingQualitySummaryRequest,
    DpmPmOperatingQualitySupportability,
)
from app.services import dpm_command_center_ai_context, dpm_command_center_supportability
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_command_center_errors import raise_manage_command_center_error
from app.services.dpm_pm_operating_quality_client_protocols import (
    DpmPmOperatingQualityClientAccessMixin,
)
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import raise_product_safe_service_error


@dataclass(frozen=True)
class DpmPmOperatingQualitySummaryContext:
    manage_status: int
    score_run: dict[str, object]
    supportability: DpmPmOperatingQualitySupportability
    summary_request: dict[str, object]
    task_payload: dict[str, object]


class DpmPmOperatingQualitySummaryServiceMixin(DpmPmOperatingQualityClientAccessMixin):
    _lotus_ai_client: LotusAiWorkflowClient | None

    async def request_pm_operating_quality_summary(
        self,
        score_run_id: str,
        request: DpmPmOperatingQualitySummaryRequest,
        correlation_id: str,
    ) -> DpmPmOperatingQualitySummaryGatewayResponse:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)
        summary_context = await self._load_pm_operating_quality_summary_context(
            score_run_id=score_run_id,
            request=request,
            correlation_id=correlation_id,
        )

        ai_status, ai_payload = await self._execute_pm_operating_quality_summary_workflow(
            lotus_ai_client=lotus_ai_client,
            score_run_id=score_run_id,
            correlation_id=correlation_id,
            summary_context=summary_context,
        )
        return self._compose_pm_operating_quality_summary_response(
            correlation_id=correlation_id,
            summary_context=summary_context,
            ai_status=ai_status,
            ai_payload=ai_payload,
        )

    async def _load_pm_operating_quality_summary_context(
        self,
        *,
        score_run_id: str,
        request: DpmPmOperatingQualitySummaryRequest,
        correlation_id: str,
    ) -> DpmPmOperatingQualitySummaryContext:
        (
            manage_status,
            manage_payload,
        ) = await self._pm_operating_quality_client.get_pm_operating_quality_score_run(
            score_run_id=score_run_id,
            correlation_id=correlation_id,
        )
        raise_manage_command_center_error(
            manage_status,
            manage_payload,
            error_code="MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR",
        )
        score_run = self._require_pm_operating_quality_score_run(
            score_run_id=score_run_id,
            manage_status=manage_status,
            manage_payload=manage_payload,
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
        return DpmPmOperatingQualitySummaryContext(
            manage_status=manage_status,
            score_run=score_run,
            supportability=supportability,
            summary_request=summary_request,
            task_payload=task_payload,
        )

    def _require_pm_operating_quality_score_run(
        self,
        *,
        score_run_id: str,
        manage_status: int,
        manage_payload: dict[str, Any],
    ) -> dict[str, object]:
        score_run = dpm_command_center_ai_context.pm_quality_score_run_from(manage_payload)
        if score_run is not None:
            return score_run
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

    async def _execute_pm_operating_quality_summary_workflow(
        self,
        *,
        lotus_ai_client: LotusAiWorkflowClient,
        score_run_id: str,
        correlation_id: str,
        summary_context: DpmPmOperatingQualitySummaryContext,
    ) -> tuple[int, dict[str, Any]]:
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
                payload=summary_context.task_payload,
                source_refs=dpm_command_center_ai_context.pm_quality_summary_source_refs(
                    summary_context.score_run
                ),
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
        return ai_status, ai_payload

    def _compose_pm_operating_quality_summary_response(
        self,
        *,
        correlation_id: str,
        summary_context: DpmPmOperatingQualitySummaryContext,
        ai_status: int,
        ai_payload: dict[str, Any],
    ) -> DpmPmOperatingQualitySummaryGatewayResponse:
        return DpmPmOperatingQualitySummaryGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=summary_context.manage_status,
            ai_upstream_status=ai_status,
            supportability=summary_context.supportability,
            score_run=summary_context.score_run,
            summary_request=summary_context.summary_request,
            data=ai_payload,
        )
