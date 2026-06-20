from typing import Any

from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmOutcomeReviewErrorDetail,
    DpmOutcomeReviewGatewayResponse,
    DpmPortfolioMemoryGatewayResponse,
)
from app.services import dpm_command_center_supportability
from app.services.ai_client_protocols import LotusAiWorkflowClient
from app.services.dpm_client_protocols import DpmCommandCenterClient
from app.services.dpm_command_center_exception_summary import (
    DpmCommandCenterExceptionSummaryMixin,
)
from app.services.dpm_command_center_outcome_narrative import (
    DpmCommandCenterOutcomeNarrativeMixin,
)
from app.services.dpm_pm_operating_quality_service import DpmPmOperatingQualityServiceMixin
from app.services.upstream_envelope import build_product_safe_upstream_status_gateway_envelope


class DpmCommandCenterService(
    DpmCommandCenterExceptionSummaryMixin,
    DpmCommandCenterOutcomeNarrativeMixin,
    DpmPmOperatingQualityServiceMixin,
):
    def __init__(
        self,
        dpm_client: DpmCommandCenterClient,
        lotus_ai_client: LotusAiWorkflowClient | None = None,
    ):
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
        return build_product_safe_upstream_status_gateway_envelope(
            DpmOutcomeReviewGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.outcome_review_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
            error_model=DpmOutcomeReviewErrorDetail,
            error_code="MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
            default_detail="lotus-manage command-center request failed",
        )

    def _compose_command_center_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmCommandCenterGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmCommandCenterGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.command_center_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
            error_model=DpmOutcomeReviewErrorDetail,
            error_code="MANAGE_COMMAND_CENTER_UPSTREAM_ERROR",
            default_detail="lotus-manage command-center request failed",
        )

    def _compose_portfolio_memory_response(
        self,
        upstream_status: int,
        upstream_payload: dict[str, Any],
        correlation_id: str,
    ) -> DpmPortfolioMemoryGatewayResponse:
        return build_product_safe_upstream_status_gateway_envelope(
            DpmPortfolioMemoryGatewayResponse,
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            supportability=dpm_command_center_supportability.portfolio_memory_supportability_from(
                upstream_payload
            ),
            upstream_payload=upstream_payload,
            error_model=DpmOutcomeReviewErrorDetail,
            error_code="MANAGE_PORTFOLIO_MEMORY_UPSTREAM_ERROR",
            default_detail="lotus-manage command-center request failed",
        )
