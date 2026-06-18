from dataclasses import dataclass
from typing import Any, NoReturn

from fastapi import HTTPException, status

from app.config import settings
from app.contracts.dpm_command_center import (
    DpmCommandCenterSupportability,
    DpmExceptionSummaryGatewayResponse,
    DpmExceptionSummaryRequest,
)
from app.services import dpm_command_center_ai_context, dpm_command_center_supportability
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_command_center_errors import raise_manage_command_center_error
from app.services.lotus_ai_workflow import (
    build_workflow_pack_task_request,
    require_lotus_ai_client,
)
from app.services.upstream_envelope import raise_product_safe_service_error


@dataclass(frozen=True)
class DpmExceptionSummaryContext:
    manage_status: int
    exception_summary_input: dict[str, object]
    supportability: DpmCommandCenterSupportability
    summary_request: dict[str, object]


class DpmCommandCenterExceptionSummaryMixin:
    _dpm_client: DpmCommandCenterClient
    _lotus_ai_client: LotusAiWorkflowClient | None

    async def request_exception_summary(
        self,
        exception_id: str,
        request: DpmExceptionSummaryRequest,
        correlation_id: str,
    ) -> DpmExceptionSummaryGatewayResponse:
        lotus_ai_client = require_lotus_ai_client(self._lotus_ai_client)
        summary_context = await self._load_exception_summary_context(
            exception_id,
            request,
            correlation_id,
        )
        ai_status, ai_payload = await self._execute_exception_summary_workflow(
            lotus_ai_client,
            exception_id,
            summary_context,
            correlation_id,
        )

        return self._compose_exception_summary_response(
            summary_context,
            ai_status,
            ai_payload,
            correlation_id,
        )

    async def _load_exception_summary_context(
        self,
        exception_id: str,
        request: DpmExceptionSummaryRequest,
        correlation_id: str,
    ) -> DpmExceptionSummaryContext:
        manage_status, manage_payload = await self._dpm_client.list_monitoring_exceptions(
            params=_exception_summary_manage_params(request),
            correlation_id=correlation_id,
        )
        raise_manage_command_center_error(
            manage_status,
            manage_payload,
            error_code="MANAGE_EXCEPTION_SUMMARY_UPSTREAM_ERROR",
        )

        exception = dpm_command_center_ai_context.find_exception(manage_payload, exception_id)
        if exception is None:
            _raise_exception_summary_not_found(exception_id, manage_status)

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
        return DpmExceptionSummaryContext(
            manage_status=manage_status,
            exception_summary_input=exception_summary_input,
            supportability=supportability,
            summary_request=summary_request,
        )

    async def _execute_exception_summary_workflow(
        self,
        lotus_ai_client: LotusAiWorkflowClient,
        exception_id: str,
        summary_context: DpmExceptionSummaryContext,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        task_payload = dpm_command_center_ai_context.exception_summary_task_payload(
            exception_summary_input=summary_context.exception_summary_input,
            summary_request=summary_context.summary_request,
            supportability=summary_context.supportability,
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
                    summary_context.exception_summary_input
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

        return ai_status, ai_payload

    def _compose_exception_summary_response(
        self,
        summary_context: DpmExceptionSummaryContext,
        ai_status: int,
        ai_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmExceptionSummaryGatewayResponse:
        return DpmExceptionSummaryGatewayResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            manage_upstream_status=summary_context.manage_status,
            ai_upstream_status=ai_status,
            supportability=summary_context.supportability,
            exception_summary_input=summary_context.exception_summary_input,
            exception_summary_request=summary_context.summary_request,
            data=ai_payload,
        )


def _exception_summary_manage_params(
    request: DpmExceptionSummaryRequest,
) -> dict[str, object]:
    return {
        "portfolio_id": request.portfolio_id,
        "mandate_id": request.mandate_id,
        "state": request.state,
        "limit": 200,
    }


def _raise_exception_summary_not_found(
    exception_id: str,
    manage_status: int,
) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "source_service": "lotus-manage",
            "upstream_status": manage_status,
            "error_code": "MANAGE_MONITORING_EXCEPTION_NOT_FOUND",
            "detail": f"Monitoring exception `{exception_id}` was not returned by lotus-manage.",
        },
    )
