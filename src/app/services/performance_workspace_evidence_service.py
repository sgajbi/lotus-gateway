from __future__ import annotations

from collections.abc import Sequence

from app.contracts.performance_evidence import PerformanceEvidenceView
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.performance_workspace_evidence import (
    EvidenceViewFetchState,
    EvidenceViewRequestContext,
    fetch_evidence_view_state,
    fetch_performance_evidence_artifact,
    resolve_evidence_view_response,
)
from app.services.performance_workspace_response import GatheredResult
from app.services.workspace_client_protocols import PerformanceWorkspaceAnalyticsClient


class PerformanceWorkspaceEvidenceServiceMixin:
    _analytics_client: PerformanceWorkspaceAnalyticsClient

    async def get_performance_evidence_artifact(
        self,
        *,
        calculation_id: str,
        artifact_name: str,
        correlation_id: str,
    ) -> tuple[bytes, str | None]:
        return await fetch_performance_evidence_artifact(
            analytics_client=self._analytics_client,
            calculation_id=calculation_id,
            artifact_name=artifact_name,
            correlation_id=correlation_id,
        )

    async def _build_evidence_view(
        self,
        *,
        portfolio_id: str,
        as_of_date: str,
        period: str,
        basis: str,
        benchmark_code: str | None,
        contract_version: str,
        correlation_id: str,
        calculations: Sequence[tuple[str, str | None]],
        source_results: Sequence[GatheredResult | None],
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> PerformanceEvidenceView | None:
        request_context = EvidenceViewRequestContext(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
            contract_version=contract_version,
            correlation_id=correlation_id,
            calculations=calculations,
            source_results=source_results,
        )
        fetch_state = await self._fetch_evidence_view_state(request_context)
        return resolve_evidence_view_response(
            context=request_context,
            fetch_state=fetch_state,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _fetch_evidence_view_state(
        self,
        context: EvidenceViewRequestContext,
    ) -> EvidenceViewFetchState:
        return await fetch_evidence_view_state(
            analytics_client=self._analytics_client,
            context=context,
        )
