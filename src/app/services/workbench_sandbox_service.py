from dataclasses import dataclass
from typing import Any

from fastapi import status

from app.config import settings
from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchPartialFailure,
    WorkbenchPolicyFeedback,
    WorkbenchProjectedPositionView,
    WorkbenchProjectedSummary,
    WorkbenchSandboxStateResponse,
)
from app.services.upstream_envelope import (
    raise_product_safe_gateway_unavailable_error,
    safe_upstream_detail,
)
from app.services.workbench_policy_feedback import (
    build_policy_idempotency_key,
    build_policy_simulation_payload,
    parse_policy_feedback_success,
    parse_policy_feedback_unavailable,
)
from app.services.workbench_projected_state import parse_projected_state
from app.services.workspace_client_protocols import (
    WorkbenchAdviseClient,
    WorkbenchCoreClient,
)


@dataclass(frozen=True)
class WorkbenchSandboxPolicyState:
    policy_feedback: WorkbenchPolicyFeedback | None
    warnings: list[str]
    partial_failures: list[WorkbenchPartialFailure]


class WorkbenchSandboxServiceMixin:
    _lotus_core_query_client: WorkbenchCoreClient
    _advise_client: WorkbenchAdviseClient

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
        include_performance_snapshot: bool = True,
        include_rebalance_snapshot: bool = True,
    ) -> WorkbenchOverviewResponse:
        raise NotImplementedError

    async def create_sandbox_session(
        self,
        portfolio_id: str,
        correlation_id: str,
        created_by: str | None,
        ttl_hours: int,
    ) -> WorkbenchSandboxStateResponse:
        status_code, payload = await self._lotus_core_query_client.create_simulation_session(
            portfolio_id=portfolio_id,
            created_by=created_by,
            ttl_hours=ttl_hours,
            correlation_id=correlation_id,
        )
        raise_product_safe_gateway_unavailable_error(
            status_code,
            payload,
            source_service="lotus-core",
            error_code="LOTUS_CORE_SIMULATION_SESSION_CREATE_FAILED",
            default_detail="Lotus Core simulation session creation failed.",
        )

        session_payload = payload.get("session", {})
        session_id = str(session_payload.get("session_id", ""))
        session_version = int(session_payload.get("version", 1))
        projected_positions, projected_summary = await self._load_projected_state(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        return WorkbenchSandboxStateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            policy_feedback=None,
            warnings=[],
            partial_failures=[],
        )

    async def apply_sandbox_changes(
        self,
        portfolio_id: str,
        session_id: str,
        correlation_id: str,
        changes: list[dict[str, Any]],
        evaluate_policy: bool,
    ) -> WorkbenchSandboxStateResponse:
        payload = await self._apply_sandbox_changes_payload(
            session_id=session_id,
            changes=changes,
            correlation_id=correlation_id,
        )
        session_version = int(payload.get("version", 1))
        projected_positions, projected_summary = await self._load_projected_state(
            session_id=session_id,
            correlation_id=correlation_id,
        )

        policy_state = await self._build_sandbox_policy_state(
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            correlation_id=correlation_id,
            evaluate_policy=evaluate_policy,
        )

        return WorkbenchSandboxStateResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            projected_summary=projected_summary,
            policy_feedback=policy_state.policy_feedback,
            warnings=policy_state.warnings,
            partial_failures=policy_state.partial_failures,
        )

    async def _apply_sandbox_changes_payload(
        self,
        *,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> dict[str, Any]:
        status_code, payload = await self._lotus_core_query_client.add_simulation_changes(
            session_id=session_id,
            changes=changes,
            correlation_id=correlation_id,
        )
        raise_product_safe_gateway_unavailable_error(
            status_code,
            payload,
            source_service="lotus-core",
            error_code="LOTUS_CORE_SIMULATION_CHANGE_APPLY_FAILED",
            default_detail="Lotus Core simulation change application failed.",
        )
        return payload

    async def _build_sandbox_policy_state(
        self,
        *,
        portfolio_id: str,
        session_id: str,
        session_version: int,
        projected_positions: list[WorkbenchProjectedPositionView],
        correlation_id: str,
        evaluate_policy: bool,
    ) -> WorkbenchSandboxPolicyState:
        warnings: list[str] = []
        partial_failures: list[WorkbenchPartialFailure] = []
        if not evaluate_policy:
            return WorkbenchSandboxPolicyState(
                policy_feedback=None,
                warnings=warnings,
                partial_failures=partial_failures,
            )
        policy_feedback = await self._evaluate_policy_feedback(
            portfolio_id=portfolio_id,
            session_id=session_id,
            session_version=session_version,
            projected_positions=projected_positions,
            correlation_id=correlation_id,
            warnings=warnings,
            partial_failures=partial_failures,
        )
        return WorkbenchSandboxPolicyState(
            policy_feedback=policy_feedback,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    async def _load_projected_state(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[list[WorkbenchProjectedPositionView], WorkbenchProjectedSummary]:
        (
            positions_status,
            positions_payload,
        ) = await self._lotus_core_query_client.get_projected_positions(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if positions_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_gateway_unavailable_error(
                positions_status,
                positions_payload,
                source_service="lotus-core",
                error_code="LOTUS_CORE_PROJECTED_POSITIONS_UNAVAILABLE",
                default_detail="Lotus Core projected positions are unavailable.",
            )

        summary_status, summary_payload = await self._lotus_core_query_client.get_projected_summary(
            session_id=session_id,
            correlation_id=correlation_id,
        )
        if summary_status >= status.HTTP_400_BAD_REQUEST:
            raise_product_safe_gateway_unavailable_error(
                summary_status,
                summary_payload,
                source_service="lotus-core",
                error_code="LOTUS_CORE_PROJECTED_SUMMARY_UNAVAILABLE",
                default_detail="Lotus Core projected summary is unavailable.",
            )

        return parse_projected_state(
            positions_payload=positions_payload,
            summary_payload=summary_payload,
        )

    async def _evaluate_policy_feedback(
        self,
        portfolio_id: str,
        session_id: str,
        session_version: int,
        projected_positions: list[WorkbenchProjectedPositionView],
        correlation_id: str,
        warnings: list[str],
        partial_failures: list[WorkbenchPartialFailure],
    ) -> WorkbenchPolicyFeedback:
        overview = await self.get_workbench_overview(
            portfolio_id=portfolio_id,
            correlation_id=correlation_id,
        )
        simulate_payload = build_policy_simulation_payload(
            portfolio_id=portfolio_id,
            base_currency=overview.portfolio.base_currency,
            projected_positions=projected_positions,
        )
        idempotency_key = build_policy_idempotency_key(
            session_id=session_id,
            session_version=session_version,
        )
        advise_status, advise_payload = await self._advise_client.simulate_proposal(
            body=simulate_payload,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )
        if advise_status >= status.HTTP_400_BAD_REQUEST:
            warnings.append("ADVISE_PROPOSAL_SIMULATION_UNAVAILABLE")
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="lotus-advise",
                    error_code=f"HTTP_{advise_status}",
                    detail=safe_upstream_detail(
                        advise_payload,
                        default_detail="proposal simulation unavailable",
                    ),
                )
            )
            return parse_policy_feedback_unavailable(advise_payload)

        return parse_policy_feedback_success(advise_payload)
