import pytest
from fastapi import HTTPException

from app.contracts.advisor_brief import (
    AdvisorBriefWorkflowPackRunReviewActionRequest,
    AdvisorBriefWorkflowPackRunReviewActionType,
)
from app.contracts.performance_workspace import (
    AttributionLevelView,
    AttributionRowView,
    AttributionSummaryView,
    ContributionPositionView,
    ContributionSummaryView,
    MoneyWeightedReturnSummary,
    PerformanceBenchmarkOptionView,
    PerformanceComparativeSummary,
    PerformanceModuleCapability,
    PerformanceWorkspaceCapabilities,
    PerformanceWorkspaceResponse,
)
from app.contracts.workbench import (
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPortfolioSummary,
)
from app.middleware.server_timing import (
    format_server_timing_header,
    reset_server_timing_metrics,
    restore_server_timing_metrics,
)
from app.services.advisor_brief_service import AdvisorBriefService

_LIVE_EXECUTION_UNAVAILABLE_DETAIL = (
    "LIVE_EXECUTION_NOT_ENABLED: Local OpenAI-compatible endpoint is not reachable from lotus-ai."
)


class _StubPerformanceWorkspaceService:
    def __init__(self, workspace: PerformanceWorkspaceResponse):
        self.workspace = workspace
        self.calls: list[dict[str, object]] = []

    async def get_performance_workspace(self, **kwargs):
        self.calls.append(kwargs)
        return self.workspace


class _StubLotusAiClient:
    def __init__(self, *, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self.payload = payload or {
            "status": "COMPLETED",
            "task_id": "explain.v1",
            "result": {
                "message": (
                    "AI summary: portfolio return exceeded benchmark over the selected period."
                ),
                "structured_output": {
                    "grounded_summary": (
                        "AI summary: portfolio return exceeded benchmark over the selected period."
                    ),
                    "talking_points": [
                        {
                            "headline": "AI-generated active-return summary.",
                            "detail": "Use Return Path to explain the benchmark gap.",
                            "tone": "warning",
                            "evidence_refs": [
                                {
                                    "metric_label": "Active Return",
                                    "metric_value": "-6.68%",
                                    "source_ref": (
                                        "lotus-gateway:workbench:PF_1001:performance-summary:YTD"
                                    ),
                                }
                            ],
                        }
                    ],
                    "recommended_actions": [
                        {
                            "label": "Review Return Path",
                            "detail": "Check period and flow context.",
                            "evidence_refs": [],
                        }
                    ],
                    "risks_and_exceptions": [
                        {
                            "headline": "Attribution evidence is partial.",
                            "detail": "Keep the narrative constrained to available source metrics.",
                            "tone": "warning",
                            "evidence_refs": [
                                {
                                    "metric_label": "Attribution",
                                    "metric_value": "Partial",
                                    "source_ref": (
                                        "lotus-gateway:workbench:PF_1001:performance-details:YTD"
                                    ),
                                }
                            ],
                        }
                    ],
                },
            },
            "audit": {
                "request_id": "req-1",
                "task_id": "explain.v1",
                "provider_mode": "openai",
                "provider_id": "text.openai",
                "adapter_kind": "OPENAI_LIVE",
                "model_id": "gpt-5.4",
                "stubbed": False,
            },
            "evidence": {
                "descriptors": [
                    {
                        "evidence_type": "source_fact_bundle",
                        "summary": "Grounded in Gateway performance workspace facts.",
                        "attributes": {"portfolio_id": "PF_1001"},
                    }
                ]
            },
        }
        self.consumer_view_status_code = 200
        self.consumer_view_payload = {
            "run_id": "packrun_advisor_brief_req-1",
            "review": {
                "allowed_actions": ["ACCEPT", "REJECT", "REVISE", "SUPERSEDE", "ABANDON"],
                "latest_review_event_at": None,
                "latest_review_actor": None,
                "review_transition_count": 0,
                "has_review_history": False,
            },
            "lineage": {"workflow_authority_owner": "lotus-gateway"},
        }
        self.operator_profile_status_code = 200
        self.operator_profile_payload = {
            "run_id": "packrun_advisor_brief_req-1",
            "runtime_state": "COMPLETED",
            "review_state": "AWAITING_REVIEW",
            "supportability_status": "ACTION_REQUIRED",
            "review_pending": True,
            "superseded": False,
            "current_summary_note": (
                "Run completed but still requires bounded human review before downstream use."
            ),
            "replacement_run_id": None,
            "findings": [
                {
                    "finding_id": "review_pending",
                    "severity": "ACTION_REQUIRED",
                    "summary": "Run is awaiting review.",
                }
            ],
        }
        self.task_flow_status_code = 200
        self.task_flow_payload = {
            "task_flows": [
                {
                    "task_flow_id": "taskflow_advisor_brief_req-1",
                    "workflow_pack_id": "advisor_brief.pack",
                    "workflow_pack_version": "v1",
                    "flow_status": "WAITING_FOR_REVIEW",
                    "current_step_id": "generate_advisor_brief",
                    "run_refs": ["packrun_advisor_brief_req-1"],
                    "review_states": {
                        "packrun_advisor_brief_req-1": "AWAITING_REVIEW",
                    },
                    "supportability_status": "ACTION_REQUIRED",
                    "replacement_lineage": [],
                    "handoff_refs": [],
                    "updated_at": "2026-04-21T03:00:00Z",
                }
            ]
        }
        self.observability_runtime_status_code = 200
        self.observability_runtime_payload = {
            "ai_surface_supportability": {
                "posture": "degraded",
                "freshness": "current",
                "supported_surface_count": 3,
                "executable_workflow_pack_count": 3,
                "action_required_surface_count": 3,
                "unavailable_surface_count": 0,
                "no_sensitive_content_telemetry": False,
                "metric_name": "lotus_ai_surface_supportability_state",
                "surfaces": [
                    {
                        "surface_id": "advisor_brief",
                        "owning_service": "lotus-advise",
                        "workflow_authority_owner": "lotus-advise",
                        "workflow_pack_ref": "advisor_brief.pack@v1",
                        "supportability_status": "ACTION_REQUIRED",
                        "model_posture": "degraded",
                        "latest_ready_run_id": None,
                        "latest_action_required_run_id": "packrun_advisor_brief_req-1",
                        "no_sensitive_content_telemetry": False,
                        "status_summary": [
                            "advisor_brief is grounded in workflow-pack runtime source "
                            "`advisor_brief.pack@v1`."
                        ],
                    }
                ],
                "status_summary": [
                    "AI surface supportability is sourced from workflow-pack runtime, "
                    "provider operations, and safety runtime."
                ],
            }
        }
        self.execute_calls: list[dict[str, object]] = []
        self.consumer_view_calls: list[dict[str, object]] = []
        self.operator_profile_calls: list[dict[str, object]] = []
        self.task_flow_calls: list[dict[str, object]] = []
        self.observability_runtime_calls: list[dict[str, object]] = []
        self.review_action_calls: list[dict[str, object]] = []
        self.review_action_status_code = 200
        self.review_action_payload = {
            "run": {
                "run_id": "packrun_advisor_brief_req-1",
                "review_state": "ACCEPTED",
            }
        }

    async def execute_workflow_pack(self, **kwargs):
        self.execute_calls.append(kwargs)
        if self.status_code != 200:
            return self.status_code, self.payload
        return self.status_code, {
            "service": "lotus-ai",
            "version": "0.1.0",
            "eligibility": {"allowed": True},
            "execution": self.payload,
            "workflow_pack_run": {"run_id": "packrun_advisor_brief_req-1"},
            "summary": [],
        }

    async def get_workflow_pack_run_consumer_view(self, **kwargs):
        self.consumer_view_calls.append(kwargs)
        return self.consumer_view_status_code, self.consumer_view_payload

    async def get_workflow_pack_run_operator_profile(self, **kwargs):
        self.operator_profile_calls.append(kwargs)
        return self.operator_profile_status_code, self.operator_profile_payload

    async def apply_workflow_pack_run_review_action(self, **kwargs):
        self.review_action_calls.append(kwargs)
        if self.review_action_status_code == 200:
            request_payload = kwargs["request_payload"]
            replacement_run_id = request_payload.get("replacement_run_id")
            action_type = request_payload["action_type"]
            self.consumer_view_payload = {
                **self.consumer_view_payload,
                "review": {
                    **self.consumer_view_payload["review"],
                    "latest_review_event_at": "2026-04-21T03:22:00Z",
                    "latest_review_actor": request_payload["reviewed_by"],
                    "review_transition_count": 1,
                    "has_review_history": True,
                },
            }
            if action_type == "ACCEPT":
                self.operator_profile_payload = {
                    **self.operator_profile_payload,
                    "review_state": "ACCEPTED",
                    "supportability_status": "READY",
                    "review_pending": False,
                    "superseded": False,
                    "replacement_run_id": None,
                    "current_summary_note": "Run accepted for bounded downstream workflow use.",
                    "findings": [],
                }
                self.task_flow_payload["task_flows"][0] = {
                    **self.task_flow_payload["task_flows"][0],
                    "flow_status": "COMPLETED",
                    "review_states": {
                        "packrun_advisor_brief_req-1": "ACCEPTED",
                    },
                    "supportability_status": "READY",
                    "handoff_refs": [
                        {
                            "handoff_id": (
                                "taskflow_advisor_brief_req-1_handoff_packrun_advisor_brief_req-1"
                            ),
                            "owner_service": "lotus-gateway",
                            "status": "READY_FOR_HANDOFF",
                            "domain_ref": None,
                        }
                    ],
                }
            elif action_type == "REVISE":
                self.operator_profile_payload = {
                    **self.operator_profile_payload,
                    "review_state": "REVISED",
                    "supportability_status": "HISTORICAL",
                    "review_pending": False,
                    "superseded": True,
                    "replacement_run_id": replacement_run_id,
                    "current_summary_note": (
                        "Run was revised in favor of a replacement advisor-brief run."
                    ),
                    "findings": [],
                }
                self.task_flow_payload["task_flows"][0] = {
                    **self.task_flow_payload["task_flows"][0],
                    "flow_status": "SUPERSEDED",
                    "review_states": {
                        "packrun_advisor_brief_req-1": "REVISED",
                    },
                    "supportability_status": "HISTORICAL",
                    "replacement_lineage": [
                        {
                            "superseded_run_id": "packrun_advisor_brief_req-1",
                            "replacement_run_id": replacement_run_id,
                            "review_action_ref": "REVISE",
                            "reason": request_payload["reason"],
                        }
                    ],
                }
            elif action_type == "SUPERSEDE":
                self.operator_profile_payload = {
                    **self.operator_profile_payload,
                    "review_state": "SUPERSEDED",
                    "supportability_status": "HISTORICAL",
                    "review_pending": False,
                    "superseded": True,
                    "replacement_run_id": replacement_run_id,
                    "current_summary_note": (
                        "Run was superseded by a replacement advisor-brief run."
                    ),
                    "findings": [],
                }
                self.task_flow_payload["task_flows"][0] = {
                    **self.task_flow_payload["task_flows"][0],
                    "flow_status": "SUPERSEDED",
                    "review_states": {
                        "packrun_advisor_brief_req-1": "SUPERSEDED",
                    },
                    "supportability_status": "HISTORICAL",
                    "replacement_lineage": [
                        {
                            "superseded_run_id": "packrun_advisor_brief_req-1",
                            "replacement_run_id": replacement_run_id,
                            "review_action_ref": "SUPERSEDE",
                            "reason": request_payload["reason"],
                        }
                    ],
                }
        return self.review_action_status_code, self.review_action_payload

    async def list_workflow_pack_task_flows(self, **kwargs):
        self.task_flow_calls.append(kwargs)
        return self.task_flow_status_code, self.task_flow_payload

    async def get_observability_runtime_status(self, **kwargs):
        self.observability_runtime_calls.append(kwargs)
        return self.observability_runtime_status_code, self.observability_runtime_payload


class _StubAdviseClient:
    def __init__(self, *, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self.payload = payload or {
            "features": [
                {
                    "key": "advise.observability.advisory_supportability",
                    "enabled": True,
                    "operational_ready": True,
                    "owner_service": "ADVISORY",
                }
            ],
            "supportability": {
                "state": "ready",
                "reason": "advisory_ready",
                "freshness_bucket": "current",
                "dependency_count": 5,
                "ready_dependency_count": 5,
                "degraded_dependency_count": 0,
                "enabled_feature_count": 9,
                "ready_feature_count": 9,
            },
        }
        self.calls: list[dict[str, object]] = []

    async def get_platform_capabilities(self, **kwargs):
        self.calls.append(kwargs)
        return self.status_code, self.payload


@pytest.mark.asyncio
async def test_advisor_brief_service_returns_ai_summary_and_source_grounded_actions():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-1",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "ready"
    assert response.summary.startswith("AI summary:")
    assert response.talking_points[0].headline == "AI-generated active-return summary."
    assert response.talking_points[0].evidence_refs[0].source_surface == "performance.return_path"
    assert response.recommended_actions[0].label == "Review Return Path"
    assert response.risks_and_exceptions[0].headline == "Attribution evidence is partial."
    assert response.risks_and_exceptions[0].evidence_refs[0].target_mode == "analysis"
    assert response.source_metrics[0].label == "Portfolio Return"
    assert response.source_metrics[0].route == (
        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
        "&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
    )
    assert response.ai_audit["request_id"] == "req-1"
    assert response.ai_audit["provider_mode"] == "openai"
    assert response.ai_audit["provider_id"] == "text.openai"
    assert response.workflow_pack_task_flow is not None
    assert response.workflow_pack_task_flow.task_flow_id == "taskflow_advisor_brief_req-1"
    assert response.workflow_pack_task_flow.flow_status == "WAITING_FOR_REVIEW"
    assert response.workflow_pack_task_flow.review_states == {
        "packrun_advisor_brief_req-1": "AWAITING_REVIEW",
    }
    assert response.ai_surface_supportability is not None
    assert response.ai_surface_supportability.feature_key == (
        "ai.observability.ai_surface_supportability"
    )
    assert response.ai_surface_supportability.state == "action_required"
    assert response.ai_surface_supportability.freshness_bucket == "fresh"
    assert response.ai_surface_supportability.metric_name == "lotus_ai_surface_supportability_state"
    assert response.ai_surface_supportability.surfaces[0].surface_id == "advisor_brief"
    assert response.ai_surface_supportability.surfaces[0].owning_service == "lotus-advise"
    assert ai_client.task_flow_calls == [
        {
            "correlation_id": "corr-1",
            "workflow_pack_id": "advisor_brief.pack",
            "caller": "lotus-gateway",
            "workflow_surface": "advisor-brief-workspace",
            "limit": 100,
        }
    ]
    assert response.ai_audit["adapter_kind"] == "OPENAI_LIVE"
    assert response.ai_audit["model_id"] == "gpt-5.4"
    assert response.ai_audit["stubbed"] is False
    assert response.ai_evidence["descriptors"][0]["evidence_type"] == "source_fact_bundle"
    assert response.workflow_pack_run is not None
    assert response.workflow_pack_run.run_id == "packrun_advisor_brief_req-1"
    assert response.workflow_pack_run.review_state == "AWAITING_REVIEW"
    assert response.workflow_pack_run.workflow_authority_owner == "lotus-gateway"
    assert response.workflow_pack_run.findings[0].finding_id == "review_pending"
    assert workspace_service.calls[0]["portfolio_id"] == "PF_1001"
    assert ai_client.execute_calls[0]["pack_id"] == "advisor_brief.pack"
    assert ai_client.execute_calls[0]["version"] == "v1"
    assert ai_client.execute_calls[0]["environment"] == "DEVELOPMENT"
    assert ai_client.execute_calls[0]["caller_identity_class"] == "BANKER_PRODUCT"
    assert ai_client.execute_calls[0]["workflow_surface"] == "advisor-brief-workspace"
    assert ai_client.execute_calls[0]["task_request"]["task_id"] == "explain.v1"
    assert ai_client.execute_calls[0]["task_request"]["expected_output_label"] == "EXPLANATION_ONLY"
    portfolio_context = ai_client.execute_calls[0]["task_request"]["context"]["payload"][
        "portfolio"
    ]
    assert portfolio_context["portfolio_id"] == "PF_1001"
    assert portfolio_context["display_label"] == "PF 1001"
    assert set(portfolio_context.keys()) == {
        "portfolio_id",
        "display_label",
        "base_currency",
        "booking_center_code",
        "client_id",
    }
    assert ai_client.execute_calls[0]["task_request"]["context"]["payload"]["benchmark"][
        "benchmark_name"
    ] == ("Private Banking Global Balanced 60/40")
    top_position = ai_client.execute_calls[0]["task_request"]["context"]["payload"]["contribution"][
        "top_positions"
    ][0]
    assert set(top_position.keys()) == {
        "display_label",
        "contribution_pct",
        "weight_avg_pct",
        "total_return_pct",
        "local_contribution_pct",
        "fx_contribution_pct",
    }
    assert top_position["display_label"] == "AAPL US"
    top_effect = ai_client.execute_calls[0]["task_request"]["context"]["payload"]["attribution"][
        "top_effects"
    ][0]
    assert set(top_effect.keys()) == {
        "segment_label",
        "total_effect_pct",
        "allocation_pct",
        "selection_pct",
        "interaction_pct",
        "portfolio_weight_avg_pct",
        "benchmark_weight_avg_pct",
        "portfolio_return_pct",
        "benchmark_return_pct",
    }
    assert ai_client.execute_calls[0]["task_request"]["context"]["source_refs"] == [
        "lotus-gateway:workbench:PF_1001:performance-summary:YTD",
        "lotus-gateway:workbench:PF_1001:performance-details:YTD",
        "lotus-performance:benchmark:PF_1001:BMK_PB_GLOBAL_BALANCED_60_40:YTD",
    ]
    assert ai_client.consumer_view_calls == [
        {"run_id": "packrun_advisor_brief_req-1", "correlation_id": "corr-1"}
    ]
    assert ai_client.operator_profile_calls == [
        {"run_id": "packrun_advisor_brief_req-1", "correlation_id": "corr-1"}
    ]
    assert ai_client.observability_runtime_calls == [{"correlation_id": "corr-1"}]


@pytest.mark.asyncio
async def test_advisor_brief_service_withholds_completed_output_with_invalid_provider_posture():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    ai_client.payload["audit"].update({"provider_mode": "disabled", "stubbed": False})
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-invalid-provider-posture",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "partial"
    assert response.summary == (
        "YTD portfolio return for PF 1001 is 1.25% versus Private Banking Global Balanced "
        "60/40 7.93%, with active return -6.68%."
    )
    assert "AI summary:" not in response.summary
    assert response.ai_audit["provider_mode"] == "unavailable"
    assert response.ai_evidence == {"descriptors": []}
    assert response.risks_and_exceptions[-1].detail == (
        "AI provider provenance could not be verified."
    )
    assert ai_client.consumer_view_calls == []
    assert ai_client.operator_profile_calls == []
    assert ai_client.task_flow_calls == []


@pytest.mark.asyncio
async def test_advisor_brief_service_hydrates_task_flow_from_bounded_long_running_demo_window():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    historical_task_flows = []
    for index in range(25):
        historical_run_id = f"packrun_advisor_brief_air_historical_{index}"
        historical_task_flows.append(
            {
                "task_flow_id": f"taskflow_advisor_brief_air_historical_{index}",
                "workflow_pack_id": "advisor_brief.pack",
                "workflow_pack_version": "v1",
                "flow_status": "COMPLETED",
                "current_step_id": None,
                "run_refs": [historical_run_id],
                "review_states": {historical_run_id: "ACCEPTED"},
                "supportability_status": "READY",
                "replacement_lineage": [],
                "handoff_refs": [],
                "updated_at": "2026-05-01T02:12:05.015702Z",
            }
        )
    ai_client.task_flow_payload = {
        "task_flows": [
            *historical_task_flows,
            {
                "task_flow_id": "taskflow_advisor_brief_req-1",
                "workflow_pack_id": "advisor_brief.pack",
                "workflow_pack_version": "v1",
                "flow_status": "WAITING_FOR_REVIEW",
                "current_step_id": "execute_workflow_pack",
                "run_refs": ["packrun_advisor_brief_req-1"],
                "review_states": {
                    "packrun_advisor_brief_req-1": "AWAITING_REVIEW",
                },
                "supportability_status": "ACTION_REQUIRED",
                "replacement_lineage": [],
                "handoff_refs": [],
                "updated_at": "2026-05-01T10:38:15.709505+08:00",
            },
        ]
    }
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-long-running-demo-window",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert ai_client.task_flow_calls[0]["limit"] == 100
    assert response.workflow_pack_task_flow is not None
    assert response.workflow_pack_task_flow.task_flow_id == "taskflow_advisor_brief_req-1"
    assert response.workflow_pack_task_flow.run_refs == ["packrun_advisor_brief_req-1"]


@pytest.mark.asyncio
async def test_advisor_brief_service_preserves_advisory_supportability_source_posture():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    advise_client = _StubAdviseClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=_StubLotusAiClient(),
        advise_client=advise_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-advise-supportability",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.advisory_supportability is not None
    assert response.advisory_supportability.model_dump(mode="json") == {
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
    assert advise_client.calls == [{"correlation_id": "corr-advise-supportability"}]


@pytest.mark.asyncio
async def test_advisor_brief_service_omits_advisory_supportability_when_source_unavailable():
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(_build_workspace()),
        lotus_ai_client=_StubLotusAiClient(),
        advise_client=_StubAdviseClient(status_code=503, payload={"detail": "paused"}),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-advise-down",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "ready"
    assert response.advisory_supportability is None


@pytest.mark.asyncio
async def test_advisor_brief_service_marks_partial_for_partial_sources_or_ai():
    workspace = _build_workspace(
        contribution_state="partial",
        attribution_state="unavailable",
        benchmark_state="partial",
    )
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(workspace),
        lotus_ai_client=_StubLotusAiClient(status_code=503, payload={"detail": "lotus-ai paused"}),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-partial",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "partial"
    assert response.ai_audit["provider_mode"] == "unavailable"
    assert response.ai_audit["provider_id"] is None
    assert response.ai_audit["adapter_kind"] is None
    assert response.ai_audit["model_id"] is None
    assert response.ai_audit["stubbed"] is True
    assert response.ai_audit["detail"] == "lotus-ai paused"
    assert response.workflow_pack_run is None
    assert [item.model_dump(mode="json") for item in response.supportability] == [
        {"label": "Portfolio", "value": "Ready", "tone": "success", "reason": None},
        {"label": "Return History", "value": "Ready", "tone": "success", "reason": None},
        {
            "label": "Contribution",
            "value": "Partial",
            "tone": "warn",
            "reason": "Contribution aggregate only.",
        },
        {
            "label": "Attribution",
            "value": "Unavailable",
            "tone": "danger",
            "reason": "Attribution unavailable.",
        },
        {"label": "Advisor Brief", "value": "Partial", "tone": "warn", "reason": None},
    ]
    assert [item.model_dump(mode="json") for item in response.risks_and_exceptions] == [
        {
            "headline": "Contribution is partial.",
            "detail": "Contribution aggregate only.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Contribution",
                    "metric_value": "Partial",
                    "source_surface": "performance.contribution",
                    "target_mode": "analysis",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
                        "&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        },
        {
            "headline": "Attribution is unavailable.",
            "detail": "Attribution unavailable.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Attribution",
                    "metric_value": "Unavailable",
                    "source_surface": "performance.attribution",
                    "target_mode": "analysis",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
                        "&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        },
        {
            "headline": "AI narrative generation is unavailable.",
            "detail": "Source-backed metrics remain available for manual review and client prep.",
            "tone": "warning",
            "evidence_refs": [
                {
                    "metric_label": "Advisor Brief",
                    "metric_value": "Unavailable",
                    "source_surface": "performance.return_path",
                    "target_mode": "summary",
                    "route": (
                        "/performance?portfolioId=PF_1001&period=YTD&detailBasis=NET"
                        "&benchmark=BMK_PB_GLOBAL_BALANCED_60_40"
                    ),
                }
            ],
        },
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_preserves_rejected_workflow_pack_run_posture():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient(
        payload={
            "status": "REJECTED",
            "task_id": "explain.v1",
            "result": {
                "message": _LIVE_EXECUTION_UNAVAILABLE_DETAIL,
                "structured_output": {},
            },
            "audit": {
                "request_id": "req-rejected-1",
                "workflow_pack_run_id": "packrun_advisor_brief_req-rejected-1",
                "task_id": "explain.v1",
                "provider_mode": "local_openai_compatible",
                "provider_id": "text.local_openai_compatible",
                "adapter_kind": "OPENAI_COMPATIBLE",
                "model_id": "gpt-4.1-mini",
                "stubbed": False,
                "detail": _LIVE_EXECUTION_UNAVAILABLE_DETAIL,
            },
            "evidence": {"descriptors": []},
        }
    )
    ai_client.consumer_view_payload = {
        "run_id": "packrun_advisor_brief_req-rejected-1",
        "review": {
            "allowed_actions": ["ACCEPT", "REJECT", "REVISE", "SUPERSEDE", "ABANDON"],
        },
        "lineage": {"workflow_authority_owner": "lotus-gateway"},
    }
    ai_client.operator_profile_payload = {
        "run_id": "packrun_advisor_brief_req-rejected-1",
        "runtime_state": "FAILED",
        "review_state": "AWAITING_REVIEW",
        "supportability_status": "ACTION_REQUIRED",
        "review_pending": True,
        "superseded": False,
        "current_summary_note": "Run failed and requires operator diagnosis before downstream use.",
        "replacement_run_id": None,
        "findings": [
            {
                "finding_id": "runtime_failed",
                "severity": "ACTION_REQUIRED",
                "summary": "Run is in failed runtime posture.",
            }
        ],
    }
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-rejected-run",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "partial"
    assert response.summary == (
        "YTD portfolio return for PF 1001 is 1.25% versus Private Banking Global Balanced 60/40 "
        "7.93%, with active return -6.68%."
    )
    assert response.ai_audit["provider_mode"] == "local_openai_compatible"
    assert response.ai_audit["workflow_pack_run_id"] == "packrun_advisor_brief_req-rejected-1"
    assert response.workflow_pack_run is not None
    assert response.workflow_pack_run.run_id == "packrun_advisor_brief_req-rejected-1"
    assert response.workflow_pack_run.supportability_status == "ACTION_REQUIRED"
    assert response.workflow_pack_run.review_state == "AWAITING_REVIEW"
    assert response.risks_and_exceptions[-1].headline == "AI narrative generation is unavailable."
    assert response.risks_and_exceptions[-1].detail == _LIVE_EXECUTION_UNAVAILABLE_DETAIL
    assert ai_client.consumer_view_calls == [
        {
            "run_id": "packrun_advisor_brief_req-rejected-1",
            "correlation_id": "corr-rejected-run",
        }
    ]
    assert ai_client.operator_profile_calls == [
        {
            "run_id": "packrun_advisor_brief_req-rejected-1",
            "correlation_id": "corr-rejected-run",
        }
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_reuses_cached_response_for_identical_request():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
        cache_ttl_seconds=60.0,
    )

    first = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-1",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )
    second = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-2",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert first.summary == second.summary
    assert len(workspace_service.calls) == 1
    assert len(ai_client.execute_calls) == 1
    assert len(ai_client.consumer_view_calls) == 1
    assert len(ai_client.operator_profile_calls) == 1
    assert len(ai_client.task_flow_calls) == 1


@pytest.mark.asyncio
async def test_advisor_brief_service_cache_key_changes_when_request_shape_changes():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
        cache_ttl_seconds=60.0,
    )

    await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-net",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )
    await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-cache-gross",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="GROSS",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert len(workspace_service.calls) == 2
    assert len(ai_client.execute_calls) == 2
    assert len(ai_client.consumer_view_calls) == 2
    assert len(ai_client.operator_profile_calls) == 2
    assert len(ai_client.task_flow_calls) == 2


@pytest.mark.asyncio
async def test_advisor_brief_service_treats_supported_capabilities_as_ready():
    workspace = _build_workspace(
        benchmark_state="supported",
        contribution_state="supported",
        attribution_state="supported",
    )
    workspace.capabilities.summary_kpis.state = "supported"
    workspace.capabilities.return_path.state = "supported"
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(workspace),
        lotus_ai_client=_StubLotusAiClient(),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-supported",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.status == "ready"
    assert [item.value for item in response.supportability] == [
        "Ready",
        "Ready",
        "Ready",
        "Ready",
        "Ready",
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_normalizes_raw_position_ids_in_fallback_copy():
    workspace = _build_workspace()
    workspace.contribution.position_rows = [
        ContributionPositionView(
            position_id="PF_1001:FO_EQ_AAPL_US",
            contribution_pct=0.30,
            weight_avg_pct=7.37,
            total_return_pct=4.31,
        ),
        ContributionPositionView(
            position_id="PF_1001:FO_CASH_USD_BOOK_OPERATING",
            contribution_pct=-0.06,
            weight_avg_pct=9.24,
            total_return_pct=0.00,
        ),
    ]
    service = AdvisorBriefService(
        performance_workspace_service=_StubPerformanceWorkspaceService(workspace),
        lotus_ai_client=_StubLotusAiClient(
            payload={
                "status": "COMPLETED",
                "task_id": "explain.v1",
                "result": {
                    "message": "Fallback summary only.",
                    "structured_output": {
                        "grounded_summary": "Fallback summary only.",
                        "talking_points": [],
                        "recommended_actions": [],
                        "risks_and_exceptions": [],
                    },
                },
                "audit": {},
                "evidence": {"descriptors": []},
            }
        ),
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-raw-position-id",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert "PF_1001:" not in response.talking_points[1].headline
    assert response.talking_points[1].headline == "Top contributor is AAPL US."
    assert response.talking_points[2].headline == "Top detractor is USD BOOK OPERATING."
    assert response.talking_points[2].detail == (
        "USD BOOK OPERATING contributed -0.06% with return 0.00%."
    )


@pytest.mark.asyncio
async def test_advisor_brief_service_omits_workflow_pack_run_when_surfaces_unavailable():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    ai_client.consumer_view_status_code = 404
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.get_performance_advisor_brief(
        portfolio_id="PF_1001",
        correlation_id="corr-run-missing",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
    )

    assert response.workflow_pack_run is None
    assert ai_client.consumer_view_calls == [
        {"run_id": "packrun_advisor_brief_req-1", "correlation_id": "corr-run-missing"}
    ]
    assert ai_client.operator_profile_calls == []


@pytest.mark.asyncio
async def test_advisor_brief_service_rejects_review_action_not_allowed_by_run_posture():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient(
        payload={
            "status": "REJECTED",
            "task_id": "explain.v1",
            "result": {
                "message": _LIVE_EXECUTION_UNAVAILABLE_DETAIL,
                "structured_output": {},
            },
            "audit": {
                "request_id": "req-not-reviewable-1",
                "workflow_pack_run_id": "packrun_advisor_brief_req-not-reviewable-1",
                "task_id": "explain.v1",
                "provider_mode": "local_openai_compatible",
                "provider_id": "text.local_openai_compatible",
                "stubbed": False,
                "detail": _LIVE_EXECUTION_UNAVAILABLE_DETAIL,
            },
            "evidence": {"descriptors": []},
        }
    )
    ai_client.consumer_view_payload = {
        "run_id": "packrun_advisor_brief_req-not-reviewable-1",
        "review": {"allowed_actions": []},
        "lineage": {"workflow_authority_owner": "lotus-gateway"},
    }
    ai_client.operator_profile_payload = {
        "run_id": "packrun_advisor_brief_req-not-reviewable-1",
        "runtime_state": "FAILED",
        "review_state": "AWAITING_REVIEW",
        "supportability_status": "ACTION_REQUIRED",
        "review_pending": True,
        "superseded": False,
        "current_summary_note": "Run failed and requires operator diagnosis.",
        "replacement_run_id": None,
        "findings": [],
    }
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.apply_performance_advisor_brief_review_action(
            portfolio_id="PF_1001",
            correlation_id="corr-not-reviewable",
            period="YTD",
            chart_frequency="monthly",
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            detail_basis="NET",
            benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
            request=AdvisorBriefWorkflowPackRunReviewActionRequest(
                action_type="ACCEPT",
                reviewed_by="live.validator.accept",
                reason="Should not proxy invalid actions to lotus-ai.",
            ),
        )

    assert exc_info.value.status_code == 409
    assert "does not allow review action `ACCEPT`" in str(exc_info.value.detail)
    assert ai_client.review_action_calls == []


@pytest.mark.asyncio
async def test_advisor_brief_service_applies_review_action_and_returns_updated_run_posture():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.apply_performance_advisor_brief_review_action(
        portfolio_id="PF_1001",
        correlation_id="corr-review-action",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        request=AdvisorBriefWorkflowPackRunReviewActionRequest(
            action_type="ACCEPT",
            reviewed_by="advisor_1",
            reason="Advisor brief accepted for bounded downstream workflow use.",
        ),
    )

    assert response.workflow_pack_run is not None
    assert response.workflow_pack_run.review_state == "ACCEPTED"
    assert response.workflow_pack_run.supportability_status == "READY"
    assert response.workflow_pack_run.review_pending is False
    assert response.workflow_pack_run.latest_review_event_at == "2026-04-21T03:22:00Z"
    assert response.workflow_pack_run.latest_review_actor == "advisor_1"
    assert response.workflow_pack_run.review_transition_count == 1
    assert response.workflow_pack_run.has_review_history is True
    assert (
        response.workflow_pack_run.current_summary_note
        == "Run accepted for bounded downstream workflow use."
    )
    assert response.workflow_pack_run.findings == []
    assert response.workflow_pack_task_flow is not None
    assert response.workflow_pack_task_flow.flow_status == "COMPLETED"
    assert response.workflow_pack_task_flow.review_states == {
        "packrun_advisor_brief_req-1": "ACCEPTED",
    }
    assert response.workflow_pack_task_flow.supportability_status == "READY"
    assert response.workflow_pack_task_flow.handoff_refs[0].status == "READY_FOR_HANDOFF"
    assert response.workflow_pack_task_flow.handoff_refs[0].owner_service == "lotus-gateway"
    assert ai_client.review_action_calls == [
        {
            "run_id": "packrun_advisor_brief_req-1",
            "correlation_id": "corr-review-action",
            "request_payload": {
                "action_type": "ACCEPT",
                "caller_app": "lotus-gateway",
                "reviewed_by": "advisor_1",
                "reason": "Advisor brief accepted for bounded downstream workflow use.",
                "replacement_run_id": None,
            },
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action_type", "expected_review_state", "expected_summary_note"),
    [
        (
            AdvisorBriefWorkflowPackRunReviewActionType.REVISE,
            "REVISED",
            "Run was revised in favor of a replacement advisor-brief run.",
        ),
        (
            AdvisorBriefWorkflowPackRunReviewActionType.SUPERSEDE,
            "SUPERSEDED",
            "Run was superseded by a replacement advisor-brief run.",
        ),
    ],
)
async def test_advisor_brief_service_preserves_replacement_lineage_for_review_transitions(
    action_type: AdvisorBriefWorkflowPackRunReviewActionType,
    expected_review_state: str,
    expected_summary_note: str,
):
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    response = await service.apply_performance_advisor_brief_review_action(
        portfolio_id="PF_1001",
        correlation_id=f"corr-{action_type.value.lower()}",
        period="YTD",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        request=AdvisorBriefWorkflowPackRunReviewActionRequest(
            action_type=action_type,
            reviewed_by="advisor_1",
            reason=f"Advisor brief {action_type.value.lower()}d in favor of a replacement run.",
            replacement_run_id="packrun_advisor_brief_req-2",
        ),
    )

    assert response.summary == (
        "AI summary: portfolio return exceeded benchmark over the selected period."
    )
    assert response.workflow_pack_run is not None
    assert response.workflow_pack_run.review_state == expected_review_state
    assert response.workflow_pack_run.supportability_status == "HISTORICAL"
    assert response.workflow_pack_run.review_pending is False
    assert response.workflow_pack_run.superseded is True
    assert response.workflow_pack_run.replacement_run_id == "packrun_advisor_brief_req-2"
    assert response.workflow_pack_run.current_summary_note == expected_summary_note
    assert response.workflow_pack_task_flow is not None
    assert response.workflow_pack_task_flow.flow_status == "SUPERSEDED"
    assert (
        response.workflow_pack_task_flow.review_states["packrun_advisor_brief_req-1"]
        == expected_review_state
    )
    assert response.workflow_pack_task_flow.supportability_status == "HISTORICAL"
    assert response.workflow_pack_task_flow.replacement_lineage[0].replacement_run_id == (
        "packrun_advisor_brief_req-2"
    )
    assert response.workflow_pack_task_flow.replacement_lineage[0].review_action_ref == action_type
    assert ai_client.review_action_calls == [
        {
            "run_id": "packrun_advisor_brief_req-1",
            "correlation_id": f"corr-{action_type.lower()}",
            "request_payload": {
                "action_type": action_type,
                "caller_app": "lotus-gateway",
                "reviewed_by": "advisor_1",
                "reason": f"Advisor brief {action_type.lower()}d in favor of a replacement run.",
                "replacement_run_id": "packrun_advisor_brief_req-2",
            },
        }
    ]


@pytest.mark.asyncio
async def test_advisor_brief_service_surfaces_lineage_conflicts_without_rewriting_posture():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    ai_client.review_action_status_code = 409
    ai_client.review_action_payload = {
        "detail": "Replacement workflow-pack run packrun_advisor_brief_req-2 is already linked.",
    }
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.apply_performance_advisor_brief_review_action(
            portfolio_id="PF_1001",
            correlation_id="corr-review-conflict",
            period="YTD",
            chart_frequency="monthly",
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            detail_basis="NET",
            benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
            request=AdvisorBriefWorkflowPackRunReviewActionRequest(
                action_type="SUPERSEDE",
                reviewed_by="advisor_1",
                reason="Replacement lineage already exists.",
                replacement_run_id="packrun_advisor_brief_req-2",
            ),
        )

    assert exc_info.value.status_code == 409
    assert (
        exc_info.value.detail
        == "Replacement workflow-pack run packrun_advisor_brief_req-2 is already linked."
    )
    assert ai_client.operator_profile_payload["review_state"] == "AWAITING_REVIEW"
    assert ai_client.operator_profile_payload["replacement_run_id"] is None


@pytest.mark.asyncio
async def test_advisor_brief_service_records_source_and_ai_server_timing_spans():
    workspace_service = _StubPerformanceWorkspaceService(_build_workspace())
    ai_client = _StubLotusAiClient()
    service = AdvisorBriefService(
        performance_workspace_service=workspace_service,
        lotus_ai_client=ai_client,
    )
    token = reset_server_timing_metrics()

    try:
        await service.get_performance_advisor_brief(
            portfolio_id="PF_1001",
            correlation_id="corr-1",
            period="YTD",
            chart_frequency="monthly",
            contribution_dimension="asset_class",
            attribution_dimension="asset_class",
            detail_basis="NET",
            benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        )

        server_timing = format_server_timing_header(1.0)
    finally:
        restore_server_timing_metrics(token)

    assert "perf-advisor-brief-source;dur=" in server_timing
    assert "perf-advisor-brief-ai;dur=" in server_timing


def _build_workspace(
    *,
    benchmark_state: str = "ready",
    contribution_state: str = "ready",
    attribution_state: str = "ready",
) -> PerformanceWorkspaceResponse:
    return PerformanceWorkspaceResponse(
        correlation_id="corr-1",
        contract_version="v1",
        portfolio_id="PF_1001",
        as_of_date="2026-04-04",
        period="YTD",
        report_start_date="2026-01-01",
        report_end_date="2026-04-04",
        chart_frequency="monthly",
        contribution_dimension="asset_class",
        attribution_dimension="asset_class",
        detail_basis="NET",
        requested_chart_frequency_supported=True,
        requested_contribution_dimension_supported=True,
        requested_attribution_dimension_supported=True,
        segment="asset_class",
        benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
        benchmark_options=[
            PerformanceBenchmarkOptionView(
                benchmark_code="BMK_PB_GLOBAL_BALANCED_60_40",
                benchmark_name="Private Banking Global Balanced 60/40",
                benchmark_currency="USD",
            )
        ],
        capabilities=PerformanceWorkspaceCapabilities(
            summary_kpis=PerformanceModuleCapability(state="ready"),
            return_path=PerformanceModuleCapability(state="ready"),
            benchmark_comparison=PerformanceModuleCapability(state=benchmark_state),
            multi_horizon_returns=PerformanceModuleCapability(state="ready"),
            contribution_ranking=PerformanceModuleCapability(state=contribution_state),
            attribution_detail=PerformanceModuleCapability(
                state=attribution_state,
                reason="Attribution unavailable." if attribution_state != "ready" else None,
            ),
            contribution_detail=PerformanceModuleCapability(
                state=contribution_state,
                reason="Contribution aggregate only." if contribution_state != "ready" else None,
            ),
            evidence=PerformanceModuleCapability(state="ready"),
        ),
        portfolio=WorkbenchPortfolioSummary(
            portfolio_id="PF_1001",
            client_id="CIF_1001",
            base_currency="USD",
            booking_center_code="SG",
        ),
        overview=WorkbenchOverviewSummary(
            market_value_base=1_087_461.0,
            cash_weight_pct=8.5,
            position_count=10,
        ),
        net_performance=PerformanceComparativeSummary(
            metric_basis="NET",
            portfolio_return_pct=1.25,
            benchmark_return_pct=7.93,
            active_return_pct=-6.68,
            benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
            end_market_value=1_087_461.0,
            net_cash_flow=14_725.0,
        ),
        gross_performance=PerformanceComparativeSummary(
            metric_basis="GROSS",
            portfolio_return_pct=1.45,
            benchmark_return_pct=7.93,
            active_return_pct=-6.48,
            benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
            end_market_value=1_087_461.0,
            net_cash_flow=14_725.0,
        ),
        money_weighted_return=MoneyWeightedReturnSummary(
            money_weighted_return_pct=1.23,
            method="XIRR",
            start_date="2026-01-01",
            end_date="2026-04-04",
        ),
        net_chart=[],
        gross_chart=[],
        contribution=ContributionSummaryView(
            metric_basis="NET",
            portfolio_contribution_pct=1.25,
            coverage_mv_pct=100.0,
            position_rows=[
                ContributionPositionView(
                    position_id="AAPL US",
                    contribution_pct=0.30,
                    weight_avg_pct=7.37,
                    total_return_pct=4.31,
                ),
                ContributionPositionView(
                    position_id="USD BOOK OPERATING",
                    contribution_pct=-0.06,
                    weight_avg_pct=9.24,
                    total_return_pct=0.00,
                ),
            ],
            levels=[],
        ),
        attribution=AttributionSummaryView(
            metric_basis="NET",
            model="BF",
            linking="Carino",
            benchmark_id="BMK_PB_GLOBAL_BALANCED_60_40",
            active_return_pct=-6.68,
            sum_of_effects_pct=-6.67,
            residual_pct=-0.01,
            levels=[
                AttributionLevelView(
                    dimension="asset_class",
                    total_effect_pct=-3.2,
                    rows=[
                        AttributionRowView(
                            key_label="Equity",
                            portfolio_weight_avg_pct=62.0,
                            benchmark_weight_avg_pct=55.0,
                            portfolio_return_pct=4.0,
                            benchmark_return_pct=8.0,
                            allocation_pct=-1.1,
                            selection_pct=-2.0,
                            interaction_pct=-0.1,
                            total_effect_pct=-3.2,
                        )
                    ],
                )
            ],
        ),
        warnings=["FOUNDATION_WARNING"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service="lotus-core",
                error_code="FOUNDATION_WARNING",
                detail="Foundation context has warnings.",
            )
        ],
    )
