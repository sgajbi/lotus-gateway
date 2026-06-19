from __future__ import annotations

from typing import Any

import pytest
from advisor_brief_test_data import build_advisor_brief_workspace

from app.contracts.advisor_brief import AdvisorBriefStatus
from app.services.advisor_brief_supportability import (
    build_advisor_brief_source_supportability,
    load_advisory_supportability,
    load_ai_surface_supportability,
    parse_ai_surface_supportability,
    resolve_advisor_brief_source_status,
)


class _AdvisorBriefAiClientStub:
    def __init__(self, *, status_code: int = 200, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.payload = payload or {
            "ai_surface_supportability": {
                "posture": "degraded",
                "freshness": "current",
                "metric_name": "lotus_ai_surface_supportability_state",
                "supported_surface_count": 2,
                "executable_workflow_pack_count": 1,
                "action_required_surface_count": 1,
                "unavailable_surface_count": 0,
                "no_sensitive_content_telemetry": True,
                "surfaces": [
                    {
                        "surface_id": "advisor_brief",
                        "owning_service": "lotus-advise",
                        "workflow_authority_owner": "lotus-advise",
                        "workflow_pack_ref": "advisor_brief.pack@v1",
                        "supportability_status": "ACTION_REQUIRED",
                        "model_posture": "degraded",
                        "latest_ready_run_id": "packrun-ready-1",
                        "latest_action_required_run_id": "packrun-action-1",
                        "no_sensitive_content_telemetry": True,
                        "status_summary": ["Review required."],
                    },
                    {"surface_id": "incomplete"},
                ],
                "status_summary": ["One AI surface requires operator action."],
            }
        }
        self.calls: list[dict[str, Any]] = []

    async def execute_workflow_pack(
        self,
        *,
        pack_id: str,
        version: str,
        environment: str,
        caller_identity_class: str,
        workflow_surface: str | None,
        task_request: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("execute_workflow_pack is not used by supportability tests")

    async def get_observability_runtime_status(
        self,
        *,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append({"correlation_id": correlation_id})
        return self.status_code, self.payload

    async def get_workflow_pack_run_consumer_view(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("get_workflow_pack_run_consumer_view is not used by these tests")

    async def get_workflow_pack_run_operator_profile(
        self,
        *,
        run_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("get_workflow_pack_run_operator_profile is not used by these tests")

    async def list_workflow_pack_task_flows(
        self,
        *,
        correlation_id: str,
        workflow_pack_id: str | None = None,
        caller: str | None = None,
        workflow_surface: str | None = None,
        limit: int = 25,
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("list_workflow_pack_task_flows is not used by these tests")

    async def apply_workflow_pack_run_review_action(
        self,
        *,
        run_id: str,
        correlation_id: str,
        request_payload: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        raise AssertionError("apply_workflow_pack_run_review_action is not used by these tests")


class _AdvisorBriefAdviseClientStub:
    def __init__(self, *, status_code: int = 200, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.payload = payload or {
            "supportability": {
                "state": "ready",
                "reason": "advisory_ready",
                "freshness_bucket": "current",
                "dependency_count": 5,
                "ready_dependency_count": 5,
                "degraded_dependency_count": 0,
                "enabled_feature_count": 9,
                "ready_feature_count": 9,
            }
        }
        self.calls: list[dict[str, Any]] = []

    async def get_platform_capabilities(
        self,
        *,
        consumer_system: str = "lotus-gateway",
        tenant_id: str = "default",
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {
                "consumer_system": consumer_system,
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
            }
        )
        return self.status_code, self.payload


def test_source_supportability_preserves_advisor_brief_readiness_rollup() -> None:
    workspace = build_advisor_brief_workspace(attribution_state="partial")

    supportability = build_advisor_brief_source_supportability(workspace=workspace)
    status = resolve_advisor_brief_source_status(
        workspace=workspace,
        supportability=supportability,
    )

    assert [item.label for item in supportability] == [
        "Portfolio",
        "Return History",
        "Contribution",
        "Attribution",
        "Advisor Brief",
    ]
    assert supportability[-1].value == "Partial"
    assert status is AdvisorBriefStatus.PARTIAL


@pytest.mark.asyncio
async def test_load_ai_surface_supportability_preserves_bounded_source_posture() -> None:
    ai_client = _AdvisorBriefAiClientStub()

    supportability = await load_ai_surface_supportability(
        lotus_ai_client=ai_client,
        correlation_id="corr-ai-supportability",
    )

    assert supportability is not None
    assert supportability.state == "action_required"
    assert supportability.freshness_bucket == "fresh"
    assert supportability.supported_surface_count == 2
    assert len(supportability.surfaces) == 1
    assert supportability.surfaces[0].surface_id == "advisor_brief"
    assert supportability.surfaces[0].workflow_authority_owner == "lotus-advise"
    assert supportability.status_summary == ["One AI surface requires operator action."]
    assert ai_client.calls == [{"correlation_id": "corr-ai-supportability"}]


@pytest.mark.asyncio
async def test_load_ai_surface_supportability_omits_unavailable_source() -> None:
    supportability = await load_ai_surface_supportability(
        lotus_ai_client=_AdvisorBriefAiClientStub(status_code=503, payload={"detail": "paused"}),
        correlation_id="corr-ai-down",
    )

    assert supportability is None


def test_parse_ai_surface_supportability_clamps_non_integer_counts() -> None:
    supportability = parse_ai_surface_supportability(
        source={
            "posture": "healthy",
            "freshness": "ready",
            "supported_surface_count": True,
            "executable_workflow_pack_count": -1,
            "action_required_surface_count": "3",
            "unavailable_surface_count": 4,
            "no_sensitive_content_telemetry": False,
        }
    )

    assert supportability.state == "ready"
    assert supportability.freshness_bucket == "fresh"
    assert supportability.supported_surface_count == 0
    assert supportability.executable_workflow_pack_count == 0
    assert supportability.action_required_surface_count == 0
    assert supportability.unavailable_surface_count == 4


@pytest.mark.asyncio
async def test_load_advisory_supportability_preserves_source_posture() -> None:
    advise_client = _AdvisorBriefAdviseClientStub()

    supportability = await load_advisory_supportability(
        advise_client=advise_client,
        correlation_id="corr-advisory-supportability",
    )

    assert supportability is not None
    assert supportability.model_dump(mode="json") == {
        "feature_key": "advise.observability.advisory_supportability",
        "state": "ready",
        "reason": "advisory_ready",
        "freshness_bucket": "current",
        "dependency_count": 5,
        "ready_dependency_count": 5,
        "degraded_dependency_count": 0,
        "enabled_feature_count": 9,
        "ready_feature_count": 9,
        "metric_name": "lotus_advise_advisory_supportability_total",
    }
    assert advise_client.calls == [
        {
            "consumer_system": "lotus-gateway",
            "tenant_id": "default",
            "correlation_id": "corr-advisory-supportability",
        }
    ]


@pytest.mark.asyncio
async def test_load_advisory_supportability_omits_absent_source() -> None:
    assert (
        await load_advisory_supportability(
            advise_client=None,
            correlation_id="corr-no-advise",
        )
        is None
    )
    assert (
        await load_advisory_supportability(
            advise_client=_AdvisorBriefAdviseClientStub(
                status_code=503,
                payload={"detail": "paused"},
            ),
            correlation_id="corr-advise-down",
        )
        is None
    )
