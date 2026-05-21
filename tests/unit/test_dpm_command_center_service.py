import pytest
from fastapi import HTTPException

from app.contracts.dpm_command_center import (
    DpmExceptionSummaryRequest,
    DpmOutcomeReviewNarrativeRequest,
    DpmPmOperatingQualitySummaryRequest,
)
from app.services.dpm_command_center_service import DpmCommandCenterService


class _FakeDpmClient:
    def __init__(self, result: tuple[int, dict]):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def create_outcome_review(self, body, correlation_id):  # noqa: ANN001
        self.calls.append({"method": "create", "body": body, "correlation_id": correlation_id})
        return self.result

    async def get_command_center(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {"method": "command_center", "params": params, "correlation_id": correlation_id}
        )
        return self.result

    async def run_monitoring_once(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {"method": "run_monitoring_once", "body": body, "correlation_id": correlation_id}
        )
        return self.result

    async def get_mandate_health(self, mandate_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "mandate_health",
                "mandate_id": mandate_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_mandate_by_portfolio(self, portfolio_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "mandate_by_portfolio",
                "portfolio_id": portfolio_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_portfolio_memory(self, portfolio_id, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "portfolio_memory",
                "portfolio_id": portfolio_id,
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_outcome_review_supportability(self, outcome_review_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "supportability",
                "outcome_review_id": outcome_review_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_outcome_review_ai_evidence_input(self, outcome_review_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "ai_evidence",
                "outcome_review_id": outcome_review_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def preview_pm_operating_quality_score_run(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {"method": "pm_quality_preview", "body": body, "correlation_id": correlation_id}
        )
        return self.result

    async def create_pm_operating_quality_score_run(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {"method": "pm_quality_create", "body": body, "correlation_id": correlation_id}
        )
        return self.result

    async def preview_pm_operating_quality_fairness_analysis(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_fairness_preview",
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def create_pm_operating_quality_fairness_analysis(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_fairness_create",
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def list_pm_operating_quality_fairness_analyses(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_fairness_analyses",
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_pm_operating_quality_fairness_analysis(  # noqa: ANN001
        self,
        fairness_analysis_id,
        correlation_id,
    ):
        self.calls.append(
            {
                "method": "pm_quality_fairness_analysis",
                "fairness_analysis_id": fairness_analysis_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def preview_pm_operating_quality_review_action(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_review_action_preview",
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def create_pm_operating_quality_review_action(self, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_review_action_create",
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def list_pm_operating_quality_review_actions(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_review_actions",
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_pm_operating_quality_review_action(  # noqa: ANN001
        self,
        review_action_id,
        correlation_id,
    ):
        self.calls.append(
            {
                "method": "pm_quality_review_action",
                "review_action_id": review_action_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def list_pm_operating_quality_score_runs(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {"method": "pm_quality_score_runs", "params": params, "correlation_id": correlation_id}
        )
        return self.result

    async def get_pm_operating_quality_score_run(self, score_run_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "pm_quality_score_run",
                "score_run_id": score_run_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def put_pm_operating_quality_policy(  # noqa: ANN001
        self,
        policy_id,
        policy_version,
        body,
        correlation_id,
    ):
        self.calls.append(
            {
                "method": "pm_quality_policy_put",
                "policy_id": policy_id,
                "policy_version": policy_version,
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def list_pm_operating_quality_policies(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {"method": "pm_quality_policies", "params": params, "correlation_id": correlation_id}
        )
        return self.result

    async def get_pm_operating_quality_policy(  # noqa: ANN001
        self,
        policy_id,
        policy_version,
        correlation_id,
    ):
        self.calls.append(
            {
                "method": "pm_quality_policy",
                "policy_id": policy_id,
                "policy_version": policy_version,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def list_monitoring_exceptions(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "list_exceptions",
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result


class _FakeLotusAiClient:
    def __init__(self, result: tuple[int, dict]):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        self.calls.append(kwargs)
        return self.result


@pytest.mark.asyncio
async def test_dpm_command_center_summary_preserves_manage_health_and_supportability() -> None:
    manage_payload = {
        "health_distribution": {"READY": 3, "PENDING_REVIEW": 1, "BLOCKED": 1},
        "evaluated_mandates": 5,
        "active_exception_count": 2,
        "latest_monitoring_run": {"monitoring_run_id": "dmr_1", "status": "SUCCEEDED"},
        "supportability": {
            "data_completeness_state": "PARTIAL",
            "partial_readiness_reasons": ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"],
            "source_run_id": "dmr_1",
            "remediation_owner": "Portfolio Operations",
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_command_center(
        filters={
            "tenant_id": "default",
            "portfolio_manager_id": "PM_SG_DPM_001",
            "health_state": "PENDING_REVIEW",
            "limit": 25,
        },
        correlation_id="corr-command-center-1",
    )

    assert response.correlation_id == "corr-command-center-1"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.supportability.state == "PARTIAL"
    assert response.supportability.data_completeness_state == "PARTIAL"
    assert response.supportability.partial_readiness_reasons == ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"]
    assert response.supportability.source_run_id == "dmr_1"
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "command_center",
            "params": {
                "tenant_id": "default",
                "portfolio_manager_id": "PM_SG_DPM_001",
                "health_state": "PENDING_REVIEW",
                "limit": 25,
            },
            "correlation_id": "corr-command-center-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_command_center_monitoring_run_forwards_body_without_book_discovery() -> None:
    manage_payload = {
        "monitoring_run_id": "dmr_1",
        "status": "SUCCEEDED",
        "mandate_results": [{"mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001"}],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.run_monitoring_once(
        body={
            "mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"],
            "as_of_date": "2026-05-03",
            "tenant_id": "default",
        },
        correlation_id="corr-command-center-run",
    )

    assert response.supportability.state == "UNKNOWN"
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "run_monitoring_once",
            "body": {
                "mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"],
                "as_of_date": "2026-05-03",
                "tenant_id": "default",
            },
            "correlation_id": "corr-command-center-run",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_command_center_mandate_health_preserves_manage_dimensions() -> None:
    manage_payload = {
        "health_snapshot_id": "mh_1",
        "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
        "health_score": 97,
        "health_state": "PENDING_REVIEW",
        "dimension_scores": [
            {
                "dimension": "SOURCE_READINESS",
                "score": 90,
                "state": "PENDING_REVIEW",
                "reason_codes": ["TAX_LOT_SOURCE_PARTIAL"],
            }
        ],
        "source_readiness_state": "READY",
        "recommended_action": "SIMULATE_REBALANCE",
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_mandate_health(
        mandate_id="MANDATE_PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-mandate-health",
    )

    assert response.supportability.state == "UNKNOWN"
    assert response.data["health_score"] == 97
    assert response.data["dimension_scores"] == manage_payload["dimension_scores"]
    assert client.calls == [
        {
            "method": "mandate_health",
            "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
            "correlation_id": "corr-mandate-health",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_command_center_mandate_supportability_uses_manage_field_gaps() -> None:
    manage_payload = {
        "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "mandate_version": "1",
        "investment_objective": (
            "Preserve and grow global balanced wealth within controlled drawdown limits."
        ),
        "benchmark_id": "BMK_PB_GLOBAL_BALANCED_60_40",
        "review_policy": {
            "review_frequency": "QUARTERLY",
            "last_review_date": "2026-03-31",
            "next_review_due_date": "2026-06-30",
        },
        "source_lineage": [
            {"product_name": "DiscretionaryMandateBinding", "data_quality_status": "ACCEPTED"},
            {"product_name": "BenchmarkAssignment", "data_quality_status": "COMPLETE"},
        ],
        "field_gap_codes": ["CLIENT_INCOME_NEED_PROFILE_NOT_YET_SOURCED"],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_mandate_by_portfolio(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        correlation_id="corr-mandate-by-portfolio",
    )

    assert response.supportability.state == "PARTIAL"
    assert response.supportability.data_completeness_state == "PARTIAL"
    assert response.supportability.partial_readiness_reasons == [
        "CLIENT_INCOME_NEED_PROFILE_NOT_YET_SOURCED"
    ]
    assert response.supportability.source_run_id == "1"
    assert response.data["benchmark_id"] == "BMK_PB_GLOBAL_BALANCED_60_40"


@pytest.mark.asyncio
async def test_dpm_portfolio_memory_preserves_manage_timeline_and_supportability() -> None:
    manage_payload = {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "event_count": 5,
        "supportability_state": "READY",
        "event_type_counts": {
            "PROOF_PACK_CREATED": 1,
            "WAVE_HANDOFF_READY": 1,
            "OUTCOME_REVIEW_CREATED": 1,
            "OUTCOME_REVIEW_EVENT": 1,
            "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION": 1,
        },
        "source_systems": ["lotus-manage", "lotus-core", "lotus-risk"],
        "reason_codes": ["SOURCE_READY", "OUTCOME_REVIEW_READY"],
        "content_hash": "sha256:portfolio-memory",
        "events": [
            {
                "event_id": "memory:outcome-review:or_1",
                "event_type": "OUTCOME_REVIEW_CREATED",
                "event_time": "2026-05-07T10:00:00Z",
                "source_refs": [{"source_system": "lotus-manage", "source_id": "or_1"}],
            }
        ],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_portfolio_memory(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        filters={"limit": 50},
        correlation_id="corr-portfolio-memory",
    )

    assert response.correlation_id == "corr-portfolio-memory"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.supportability.authority == "lotus-manage:RFC-0040/RFC-0041/RFC-0042"
    assert response.supportability.state == "READY"
    assert response.supportability.event_count == 5
    assert response.supportability.event_type_counts["WAVE_HANDOFF_READY"] == 1
    assert (
        response.supportability.event_type_counts["BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION"]
        == 1
    )
    assert response.supportability.source_systems == ["lotus-manage", "lotus-core", "lotus-risk"]
    assert response.supportability.reason_codes == ["SOURCE_READY", "OUTCOME_REVIEW_READY"]
    assert response.supportability.content_hash == "sha256:portfolio-memory"
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "portfolio_memory",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "params": {"limit": 50},
            "correlation_id": "corr-portfolio-memory",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_portfolio_memory_preserves_campaign_assignment_transition_event() -> None:
    transition_event = {
        "event_id": (
            "memory:campaign_definition:campaign_001:v1:"
            "assignment-task:task_001:transition:transition_001"
        ),
        "event_type": "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION",
        "event_time": "2026-05-21T08:15:00Z",
        "actor": "ops_lead",
        "source_system": "lotus-manage",
        "source_type": "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION",
        "source_id": "transition_001",
        "status": "IN_PROGRESS",
        "supportability_state": "PENDING_REVIEW",
        "summary": "Bounded Manage transition summary from source truth.",
        "reason_codes": [
            "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION_RECORDED",
            "ACKNOWLEDGE",
            "IN_PROGRESS",
            "ON_TRACK",
        ],
        "source_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "BulkReviewCampaignDefinition",
                "source_id": "campaign_001:v1",
                "content_hash": "sha256:campaign-definition",
            }
        ],
        "artifact_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK",
                "source_id": "task_001",
                "content_hash": "sha256:assignment-task",
            }
        ],
        "content_hash": "sha256:assignment-task-transition",
        "metadata": {
            "task_ref": "task-ref-001",
            "assignment_task_id": "task_001",
            "transition_type": "ACKNOWLEDGE",
            "from_status": "OPEN",
            "to_status": "IN_PROGRESS",
            "sla_posture": "ON_TRACK",
            "supportability_state": "PENDING_REVIEW",
            "transition_reason_projected": False,
            "external_workflow_orchestration_claimed": False,
            "client_contact_claimed": False,
            "external_execution_claimed": False,
            "transition_reason": "unsafe upstream rationale stays source-owned",
            "raw_rationale": "unsafe raw rationale stays source-owned",
            "client_contact": "message client",
            "oms_action": "route order",
            "order_instruction": "buy security",
        },
    }
    manage_payload = {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "event_count": 1,
        "supportability_state": "READY",
        "event_type_counts": {
            "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION": 1,
        },
        "source_systems": ["lotus-manage"],
        "reason_codes": ["BULK_REVIEW_CAMPAIGN_WORKFLOW_SOURCE_EVENTS_SUPPORTED"],
        "content_hash": "sha256:portfolio-memory",
        "events": [transition_event],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_portfolio_memory(
        portfolio_id="PB_SG_GLOBAL_BAL_001",
        filters={"limit": 25},
        correlation_id="corr-campaign-assignment-task-transition",
    )

    assert (
        response.supportability.event_type_counts["BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION"]
        == 1
    )
    assert response.data["events"][0] == transition_event
    assert response.data["events"][0]["source_refs"] == transition_event["source_refs"]
    assert response.data["events"][0]["artifact_refs"] == transition_event["artifact_refs"]
    assert response.data["events"][0]["content_hash"] == "sha256:assignment-task-transition"
    assert response.data["events"][0]["metadata"]["transition_reason_projected"] is False
    assert response.data["events"][0]["metadata"]["client_contact_claimed"] is False
    assert response.data["events"][0]["metadata"]["external_execution_claimed"] is False
    assert client.calls == [
        {
            "method": "portfolio_memory",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "params": {"limit": 25},
            "correlation_id": "corr-campaign-assignment-task-transition",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_portfolio_memory_manage_errors_are_product_safe() -> None:
    client = _FakeDpmClient((404, {"detail": "portfolio memory not found"}))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_portfolio_memory(
            portfolio_id="missing",
            filters={"limit": 25},
            correlation_id="corr-portfolio-memory-error",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 404,
        "error_code": "MANAGE_PORTFOLIO_MEMORY_UPSTREAM_ERROR",
        "detail": "portfolio memory not found",
    }


@pytest.mark.asyncio
async def test_dpm_command_center_manage_errors_are_product_safe() -> None:
    client = _FakeDpmClient((422, {"detail": "invalid health_state"}))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_command_center(
            filters={"health_state": "NOT_REAL"},
            correlation_id="corr-command-center-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 422,
        "error_code": "MANAGE_COMMAND_CENTER_UPSTREAM_ERROR",
        "detail": "invalid health_state",
    }


@pytest.mark.asyncio
async def test_dpm_command_center_preserves_manage_payload_and_supportability() -> None:
    manage_payload = {
        "outcome_review_id": "or_1",
        "state": "READY",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "expected_snapshot_hash": "sha256:expected",
        "supportability": {
            "state": "SUPPORTED",
            "reason_codes": ["READY_FOR_REPORT_INPUT"],
            "blocked_actions": [],
            "remediation_owner": "Portfolio Operations",
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.create_outcome_review(
        body={"rebalance_run_id": "rr_1"},
        correlation_id="corr-1",
    )

    assert response.correlation_id == "corr-1"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.supportability.state == "SUPPORTED"
    assert response.supportability.reason_codes == ["READY_FOR_REPORT_INPUT"]
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "create",
            "body": {"rebalance_run_id": "rr_1"},
            "correlation_id": "corr-1",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_command_center_supportability_endpoint_handles_flat_payload() -> None:
    client = _FakeDpmClient(
        (
            200,
            {
                "state": "DEGRADED",
                "reasonCodes": ["SOURCE_STALE"],
                "blockedActions": ["CREATE_REPORT_INPUT"],
            },
        )
    )
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_outcome_review_supportability(
        outcome_review_id="or_1",
        correlation_id="corr-2",
    )

    assert response.supportability.state == "DEGRADED"
    assert response.supportability.reason_codes == ["SOURCE_STALE"]
    assert response.supportability.blocked_actions == ["CREATE_REPORT_INPUT"]


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["DEGRADED", "BLOCKED", "UNSUPPORTED", "UNAVAILABLE"])
async def test_dpm_command_center_preserves_manage_supportability_states(state: str) -> None:
    client = _FakeDpmClient(
        (
            200,
            {
                "outcome_review_id": "or_1",
                "supportability": {
                    "state": state,
                    "reason_codes": [f"{state}_REASON"],
                    "blocked_actions": ["CREATE_REPORT_INPUT"] if state == "BLOCKED" else [],
                },
            },
        )
    )
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.create_outcome_review(
        body={"rebalance_run_id": "rr_1"},
        correlation_id=f"corr-{state.lower()}",
    )

    assert response.supportability.state == state
    assert response.supportability.reason_codes == [f"{state}_REASON"]
    if state == "BLOCKED":
        assert response.supportability.blocked_actions == ["CREATE_REPORT_INPUT"]


@pytest.mark.asyncio
async def test_dpm_command_center_forwards_manage_errors_as_product_safe_detail() -> None:
    client = _FakeDpmClient((409, {"detail": "execution evidence incomplete"}))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.create_outcome_review(
            body={"rebalance_run_id": "rr_1"}, correlation_id="corr-3"
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 409,
        "error_code": "MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
        "detail": "execution evidence incomplete",
    }


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_preview_preserves_manage_score_run() -> None:
    manage_payload = {
        "score_run": {
            "product_name": "PmOperatingQualityScoreRun",
            "product_version": "v1",
            "score_run_id": "pmq_run_001",
            "pm_id": "PM_SG_DPM_001",
            "book_id": "BOOK_SG_BALANCED_DPM",
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "state": "READY",
            "score": "86.5",
            "reason_codes": ["PM_QUALITY_READY"],
            "forbidden_uses": [
                "compensation_decision",
                "hr_decision",
                "conduct_enforcement",
                "autonomous_pm_ranking",
            ],
        }
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.preview_pm_operating_quality_score_run(
        body={"pm_id": "PM_SG_DPM_001", "policy_id": "pmq_sg_dpm"},
        correlation_id="corr-pmq-preview",
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042/PM_OPERATING_QUALITY"
    assert response.supportability.state == "READY"
    assert response.supportability.policy_id == "pmq_sg_dpm"
    assert response.supportability.policy_version == "2026.05"
    assert response.supportability.score_run_id == "pmq_run_001"
    assert response.supportability.reason_codes == ["PM_QUALITY_READY"]
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "pm_quality_preview",
            "body": {"pm_id": "PM_SG_DPM_001", "policy_id": "pmq_sg_dpm"},
            "correlation_id": "corr-pmq-preview",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_policy_routes_preserve_manage_policy() -> None:
    manage_payload = {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "enabled": True,
        "as_of_date": "2026-05-12",
        "reason_codes": ["POLICY_APPROVED"],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.put_pm_operating_quality_policy(
        policy_id="pmq_sg_dpm",
        policy_version="2026.05",
        body=manage_payload,
        correlation_id="corr-pmq-policy",
    )

    assert response.supportability.policy_id == "pmq_sg_dpm"
    assert response.supportability.policy_version == "2026.05"
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "pm_quality_policy_put",
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "body": manage_payload,
            "correlation_id": "corr-pmq-policy",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_fairness_preview_preserves_manage_analysis() -> None:
    manage_payload = {
        "fairness_analysis": {
            "product_name": "PmOperatingQualityFairnessAnalysis",
            "product_version": "v1",
            "fairness_analysis_id": "pmq_fair_001",
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "as_of_date": "2026-05-13",
            "state": "PENDING_REVIEW",
            "minimum_segment_score_run_count": 2,
            "maximum_average_score_spread": "15.00",
            "observed_average_score_spread": "31.00",
            "reason_codes": ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"],
            "blocked_actions": ["CREATE_SCORE_RUN"],
            "forbidden_uses": [
                "protected_class_inference",
                "autonomous_pm_ranking",
                "hr_decision",
                "compensation_decision",
                "conduct_enforcement",
            ],
            "segment_results": [
                {
                    "segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED",
                    "segment_type": "MANDATE_TYPE",
                    "display_name": "Discretionary Balanced",
                    "state": "REVIEW_REQUIRED",
                    "score_run_ids": ["pmq_run_001", "pmq_run_002"],
                    "score_run_refs": [
                        {
                            "source_system": "lotus-manage",
                            "source_product": "PmOperatingQualityScoreRun",
                            "source_id": "pmq_run_001",
                        }
                    ],
                    "source_refs": [
                        {
                            "source_system": "lotus-core",
                            "source_product": "MandateSegment",
                            "source_id": "disc_balanced",
                        }
                    ],
                }
            ],
            "source_refs": [
                {
                    "source_system": "lotus-manage",
                    "source_product": "PmOperatingQualityScoreRun",
                    "source_id": "pmq_run_001",
                }
            ],
        }
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    body = {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "as_of_date": "2026-05-13",
        "score_run_ids": ["pmq_run_001", "pmq_run_002"],
        "segments": [
            {
                "segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED",
                "segment_type": "MANDATE_TYPE",
                "display_name": "Discretionary Balanced",
                "score_run_ids": ["pmq_run_001", "pmq_run_002"],
                "source_refs": [
                    {
                        "source_system": "lotus-core",
                        "source_product": "MandateSegment",
                        "source_id": "disc_balanced",
                    }
                ],
            }
        ],
    }
    response = await service.preview_pm_operating_quality_fairness_analysis(
        body=body,
        correlation_id="corr-pmq-fairness",
    )

    assert response.source_service == "lotus-manage"
    assert response.supportability.authority == "lotus-manage:RFC-0042/PM_OPERATING_QUALITY"
    assert response.supportability.state == "PENDING_REVIEW"
    assert response.supportability.policy_id == "pmq_sg_dpm"
    assert response.supportability.policy_version == "2026.05"
    assert response.supportability.score_run_id is None
    assert response.supportability.fairness_analysis_id == "pmq_fair_001"
    assert response.supportability.reason_codes == ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"]
    assert response.supportability.blocked_actions == ["CREATE_SCORE_RUN"]
    assert response.data == manage_payload
    analysis = response.data["fairness_analysis"]
    assert analysis["minimum_segment_score_run_count"] == 2
    assert analysis["maximum_average_score_spread"] == "15.00"
    assert analysis["observed_average_score_spread"] == "31.00"
    assert analysis["forbidden_uses"] == [
        "protected_class_inference",
        "autonomous_pm_ranking",
        "hr_decision",
        "compensation_decision",
        "conduct_enforcement",
    ]
    assert analysis["segment_results"][0]["source_refs"] == [
        {
            "source_system": "lotus-core",
            "source_product": "MandateSegment",
            "source_id": "disc_balanced",
        }
    ]
    assert client.calls == [
        {
            "method": "pm_quality_fairness_preview",
            "body": body,
            "correlation_id": "corr-pmq-fairness",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_fairness_lifecycle_preserves_manage_payloads() -> None:
    create_payload = {
        "fairness_analysis": {
            "fairness_analysis_id": "pmq_fair_001",
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "state": "PENDING_REVIEW",
            "reason_codes": ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"],
            "blocked_actions": ["CREATE_SCORE_RUN"],
        }
    }
    create_client = _FakeDpmClient((201, create_payload))
    create_service = DpmCommandCenterService(dpm_client=create_client)  # type: ignore[arg-type]
    body = {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "score_run_ids": ["pmq_run_001", "pmq_run_002"],
        "segments": [],
    }

    created = await create_service.create_pm_operating_quality_fairness_analysis(
        body=body,
        correlation_id="corr-pmq-fairness-create",
    )

    assert created.upstream_status == 201
    assert created.supportability.fairness_analysis_id == "pmq_fair_001"
    assert created.data == create_payload
    assert create_client.calls == [
        {
            "method": "pm_quality_fairness_create",
            "body": body,
            "correlation_id": "corr-pmq-fairness-create",
        }
    ]

    list_payload = {
        "count": 1,
        "fairness_analyses": [
            {
                "fairness_analysis_id": "pmq_fair_001",
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "state": "PENDING_REVIEW",
                "reason_codes": ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"],
            }
        ],
    }
    list_client = _FakeDpmClient((200, list_payload))
    list_service = DpmCommandCenterService(dpm_client=list_client)  # type: ignore[arg-type]

    listed = await list_service.list_pm_operating_quality_fairness_analyses(
        filters={"policy_id": "pmq_sg_dpm", "limit": 50, "offset": 0},
        correlation_id="corr-pmq-fairness-list",
    )

    assert listed.supportability.count == 1
    assert listed.supportability.policy_id == "pmq_sg_dpm"
    assert listed.supportability.fairness_analysis_id == "pmq_fair_001"
    assert listed.data == list_payload
    assert list_client.calls == [
        {
            "method": "pm_quality_fairness_analyses",
            "params": {"policy_id": "pmq_sg_dpm", "limit": 50, "offset": 0},
            "correlation_id": "corr-pmq-fairness-list",
        }
    ]

    get_client = _FakeDpmClient((200, create_payload))
    get_service = DpmCommandCenterService(dpm_client=get_client)  # type: ignore[arg-type]

    fetched = await get_service.get_pm_operating_quality_fairness_analysis(
        fairness_analysis_id="pmq_fair_001",
        correlation_id="corr-pmq-fairness-get",
    )

    assert fetched.supportability.fairness_analysis_id == "pmq_fair_001"
    assert fetched.data == create_payload
    assert get_client.calls == [
        {
            "method": "pm_quality_fairness_analysis",
            "fairness_analysis_id": "pmq_fair_001",
            "correlation_id": "corr-pmq-fairness-get",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_review_action_lifecycle_preserves_manage_payloads() -> None:
    action_payload = {
        "review_action": {
            "review_action_id": "pmq_review_001",
            "review_action_ref": "PMQ-REVIEW-2026-05-001",
            "target_type": "SCORE_RUN",
            "target_id": "pmq_run_001",
            "target_content_hash": "sha256:pmq-run-001",
            "policy_id": "pmq_sg_dpm",
            "policy_version": "2026.05",
            "as_of_date": "2026-05-20",
            "action_type": "REQUEST_EVIDENCE_REMEDIATION",
            "action_state": "REVIEW_REQUIRED",
            "review_reason": "Evidence remediation required before supervisory closure.",
            "actor_id": "ops",
            "reason_codes": [
                "PM_QUALITY_REVIEW_ACTION_REQUEST_EVIDENCE_REMEDIATION",
                "PM_QUALITY_REVIEW_ACTION_STATE_REVIEW_REQUIRED",
            ],
            "source_refs": [
                {
                    "source_system": "lotus-manage",
                    "source_type": "PmOperatingQualityScoreRun",
                    "source_id": "pmq_run_001",
                }
            ],
            "forbidden_uses": [
                "compensation_decision",
                "hr_decision",
                "conduct_enforcement",
                "client_contact",
                "trade_approval",
                "order_routing",
                "oms_execution",
                "autonomous_pm_ranking",
            ],
            "operating_boundaries": [
                "IMMUTABLE_REVIEW_ACTION_LEDGER",
                "NO_SCORE_RECALCULATION",
                "NO_FAIRNESS_RECOMPUTATION",
                "NO_PM_RANKING",
                "NO_HR_COMPENSATION_OR_CONDUCT_DECISION",
                "NO_CLIENT_CONTACT",
                "NO_TRADE_APPROVAL",
                "NO_ORDER_OR_OMS_EXECUTION",
            ],
        }
    }
    body = {
        "target_type": "SCORE_RUN",
        "target_id": "pmq_run_001",
        "action_type": "REQUEST_EVIDENCE_REMEDIATION",
        "review_action_ref": "PMQ-REVIEW-2026-05-001",
        "review_reason": "Evidence remediation required before supervisory closure.",
        "actor_id": "ops",
        "source_refs": [],
    }
    preview_client = _FakeDpmClient((200, action_payload))
    preview_service = DpmCommandCenterService(dpm_client=preview_client)  # type: ignore[arg-type]

    previewed = await preview_service.preview_pm_operating_quality_review_action(
        body=body,
        correlation_id="corr-pmq-review-preview",
    )

    assert previewed.supportability.review_action_id == "pmq_review_001"
    assert previewed.supportability.state == "REVIEW_REQUIRED"
    assert previewed.data == action_payload
    assert preview_client.calls == [
        {
            "method": "pm_quality_review_action_preview",
            "body": body,
            "correlation_id": "corr-pmq-review-preview",
        }
    ]

    create_client = _FakeDpmClient((201, action_payload))
    create_service = DpmCommandCenterService(dpm_client=create_client)  # type: ignore[arg-type]
    created = await create_service.create_pm_operating_quality_review_action(
        body=body,
        correlation_id="corr-pmq-review-create",
    )

    assert created.upstream_status == 201
    assert created.supportability.review_action_id == "pmq_review_001"
    assert created.data["review_action"]["review_reason"] == (
        "Evidence remediation required before supervisory closure."
    )
    assert create_client.calls == [
        {
            "method": "pm_quality_review_action_create",
            "body": body,
            "correlation_id": "corr-pmq-review-create",
        }
    ]

    list_payload = {
        "count": 1,
        "review_actions": [action_payload["review_action"]],
        "limit": 50,
        "offset": 0,
    }
    list_client = _FakeDpmClient((200, list_payload))
    list_service = DpmCommandCenterService(dpm_client=list_client)  # type: ignore[arg-type]
    listed = await list_service.list_pm_operating_quality_review_actions(
        filters={"target_type": "SCORE_RUN", "action_state": "REVIEW_REQUIRED", "limit": 50},
        correlation_id="corr-pmq-review-list",
    )

    assert listed.supportability.count == 1
    assert listed.supportability.review_action_id == "pmq_review_001"
    assert listed.data == list_payload
    assert list_client.calls == [
        {
            "method": "pm_quality_review_actions",
            "params": {"target_type": "SCORE_RUN", "action_state": "REVIEW_REQUIRED", "limit": 50},
            "correlation_id": "corr-pmq-review-list",
        }
    ]

    get_client = _FakeDpmClient((200, action_payload))
    get_service = DpmCommandCenterService(dpm_client=get_client)  # type: ignore[arg-type]
    fetched = await get_service.get_pm_operating_quality_review_action(
        review_action_id="pmq_review_001",
        correlation_id="corr-pmq-review-get",
    )

    assert fetched.supportability.review_action_id == "pmq_review_001"
    assert fetched.data == action_payload
    assert get_client.calls == [
        {
            "method": "pm_quality_review_action",
            "review_action_id": "pmq_review_001",
            "correlation_id": "corr-pmq-review-get",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_manage_errors_are_product_safe() -> None:
    client = _FakeDpmClient((422, {"detail": "PM_QUALITY_GOVERNANCE_APPROVAL_REQUIRED"}))
    service = DpmCommandCenterService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.create_pm_operating_quality_score_run(
            body={"pm_id": "PM_SG_DPM_001"},
            correlation_id="corr-pmq-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 422,
        "error_code": "MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR",
        "detail": "PM_QUALITY_GOVERNANCE_APPROVAL_REQUIRED",
    }


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_summary_uses_manage_score_run_and_lotus_ai() -> None:
    manage_payload = {
        "score_run": _pm_quality_score_run(),
        "portfolio_memory_context": {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "event_count": 1,
            "events": [
                {
                    "event_id": "pmq-memory-1",
                    "event_type": "PM_QUALITY_SCORE_RUN",
                    "source_refs": [
                        {
                            "source_system": "lotus-manage",
                            "source_type": "PmOperatingQualityScoreRun",
                            "source_id": "pmq_run_001",
                        }
                    ],
                }
            ],
        },
    }
    dpm_client = _FakeDpmClient((200, manage_payload))
    ai_client = _FakeLotusAiClient(
        (
            200,
            {
                "execution": {
                    "status": "COMPLETED",
                    "audit": {"workflow_pack_run_id": "packrun_pmq_1"},
                    "result": {
                        "structured_output": {
                            "workflow_pack_family": "pm_quality_summary",
                            "summary_status": "REVIEW_REQUIRED",
                        }
                    },
                },
                "workflow_pack_run": {
                    "run_id": "packrun_pmq_1",
                    "workflow_authority_owner": "lotus-manage",
                },
            },
        )
    )
    service = DpmCommandCenterService(
        dpm_client=dpm_client,  # type: ignore[arg-type]
        lotus_ai_client=ai_client,  # type: ignore[arg-type]
    )

    response = await service.request_pm_operating_quality_summary(
        score_run_id="pmq_run_001",
        request=DpmPmOperatingQualitySummaryRequest(
            requested_outputs=["score_run_summary", "support_references"],
            audience=["portfolio_manager", "investment_control"],
        ),
        correlation_id="corr-pmq-summary",
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.manage_upstream_status == 200
    assert response.ai_upstream_status == 200
    assert response.supportability.score_run_id == "pmq_run_001"
    assert response.score_run["score_run_id"] == "pmq_run_001"
    assert response.summary_request == {
        "requested_outputs": ["score_run_summary", "support_references"],
        "audience": ["portfolio_manager", "investment_control"],
    }
    assert dpm_client.calls == [
        {
            "method": "pm_quality_score_run",
            "score_run_id": "pmq_run_001",
            "correlation_id": "corr-pmq-summary",
        }
    ]
    ai_call = ai_client.calls[0]
    assert ai_call["pack_id"] == "pm_quality_summary.pack"
    assert ai_call["version"] == "v1"
    assert ai_call["workflow_surface"] == "dpm-pm-quality-ai-evidence"
    assert ai_call["correlation_id"] == "corr-pmq-summary"
    task_request = ai_call["task_request"]
    assert task_request["caller"] == {
        "caller_app": "lotus-gateway",
        "correlation_id": "corr-pmq-summary",
    }
    payload = task_request["context"]["payload"]
    assert payload["score_run"] == manage_payload["score_run"]
    assert payload["summary_request"] == response.summary_request
    assert payload["supportability"]["requires_human_review"] is True
    assert "rank_portfolio_managers" in payload["supportability"]["forbidden_actions"]
    assert "compensation_decision" in payload["supportability"]["unsupported_claims"]
    assert payload["portfolio_memory_context"] == manage_payload["portfolio_memory_context"]
    assert "lotus-manage:pm-quality-score-run:pmq_run_001" in task_request["context"]["source_refs"]
    assert response.data["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


@pytest.mark.asyncio
async def test_dpm_pm_operating_quality_summary_preserves_lotus_ai_errors() -> None:
    dpm_client = _FakeDpmClient((200, {"score_run": _pm_quality_score_run()}))
    ai_client = _FakeLotusAiClient((422, {"detail": "pm ranking output blocked"}))
    service = DpmCommandCenterService(
        dpm_client=dpm_client,  # type: ignore[arg-type]
        lotus_ai_client=ai_client,  # type: ignore[arg-type]
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_pm_operating_quality_summary(
            score_run_id="pmq_run_001",
            request=DpmPmOperatingQualitySummaryRequest(),
            correlation_id="corr-pmq-summary-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-ai",
        "upstream_status": 422,
        "error_code": "AI_PM_OPERATING_QUALITY_SUMMARY_UPSTREAM_ERROR",
        "detail": "pm ranking output blocked",
    }


def test_dpm_pm_operating_quality_summary_rejects_unsupported_request_labels() -> None:
    with pytest.raises(ValueError, match="Unsupported PM quality summary outputs requested"):
        DpmPmOperatingQualitySummaryRequest(
            requested_outputs=["score_run_summary", "pm_ranking"],
            audience=["portfolio_manager"],
        )

    with pytest.raises(ValueError, match="Unsupported PM quality summary audiences requested"):
        DpmPmOperatingQualitySummaryRequest(
            requested_outputs=["score_run_summary"],
            audience=["portfolio_manager", "hr_committee"],
        )


@pytest.mark.asyncio
async def test_dpm_command_center_requests_ai_narrative_from_manage_evidence_only() -> None:
    ai_evidence = _outcome_ai_evidence()
    dpm_client = _FakeDpmClient((200, ai_evidence))
    ai_client = _FakeLotusAiClient(
        (
            200,
            {
                "execution": {
                    "status": "COMPLETED",
                    "audit": {"workflow_pack_run_id": "packrun_outcome_1"},
                    "result": {
                        "structured_output": {
                            "outcome_review_narrative_status": "REVIEW_REQUIRED",
                            "evidence_content_hash": "sha256:outcome-ai-evidence-001",
                        }
                    },
                },
                "workflow_pack_run": {
                    "run_id": "packrun_outcome_1",
                    "workflow_authority_owner": "lotus-manage",
                },
            },
        )
    )
    service = DpmCommandCenterService(  # type: ignore[arg-type]
        dpm_client=dpm_client,
        lotus_ai_client=ai_client,
    )

    response = await service.request_outcome_review_ai_narrative(
        outcome_review_id="or_1",
        request=DpmOutcomeReviewNarrativeRequest(
            requested_outputs=["pm_summary", "evidence_gaps"],
            audience=["pm"],
        ),
        correlation_id="corr-ai-narrative-1",
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.manage_upstream_status == 200
    assert response.ai_upstream_status == 200
    assert response.ai_evidence_input == ai_evidence
    assert response.ai_evidence_input["client_communication_boundary"] == (
        _client_communication_boundary()
    )
    assert response.data["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"
    assert dpm_client.calls == [
        {
            "method": "ai_evidence",
            "outcome_review_id": "or_1",
            "correlation_id": "corr-ai-narrative-1",
        }
    ]
    [ai_call] = ai_client.calls
    assert ai_call["pack_id"] == "outcome_review_narrative.pack"
    assert ai_call["workflow_surface"] == "dpm-outcome-review-ai-evidence"
    assert ai_call["correlation_id"] == "corr-ai-narrative-1"
    task_request = ai_call["task_request"]
    assert task_request["caller"]["caller_app"] == "lotus-gateway"
    assert task_request["context"]["payload"]["ai_evidence_input"] == ai_evidence
    assert (
        task_request["context"]["payload"]["ai_evidence_input"]["client_communication_boundary"]
        == _client_communication_boundary()
    )
    assert task_request["context"]["payload"]["narrative_request"] == {
        "requested_outputs": ["pm_summary", "evidence_gaps"],
        "audience": ["pm"],
    }
    assert "lotus-manage:outcome-review:or_1" in task_request["context"]["source_refs"]


@pytest.mark.asyncio
async def test_dpm_command_center_ai_narrative_preserves_ai_guardrail_failure() -> None:
    service = DpmCommandCenterService(  # type: ignore[arg-type]
        dpm_client=_FakeDpmClient((200, _outcome_ai_evidence())),
        lotus_ai_client=_FakeLotusAiClient(
            (
                422,
                {
                    "detail": (
                        "OUTCOME_REVIEW_NARRATIVE_GUARDRAIL_BLOCKED: "
                        "Forbidden narrative outputs requested: pm_score."
                    )
                },
            )
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_outcome_review_ai_narrative(
            outcome_review_id="or_1",
            request=DpmOutcomeReviewNarrativeRequest(
                requested_outputs=["pm_score"],
                audience=["pm"],
            ),
            correlation_id="corr-ai-narrative-blocked",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["source_service"] == "lotus-ai"
    assert exc_info.value.detail["error_code"] == "AI_OUTCOME_REVIEW_NARRATIVE_UPSTREAM_ERROR"
    assert "OUTCOME_REVIEW_NARRATIVE_GUARDRAIL_BLOCKED" in exc_info.value.detail["detail"]


@pytest.mark.asyncio
async def test_dpm_command_center_requests_exception_summary_from_manage_exception_only() -> None:
    dpm_client = _FakeDpmClient((200, _exception_page()))
    ai_client = _FakeLotusAiClient(
        (
            200,
            {
                "execution": {
                    "status": "COMPLETED",
                    "audit": {"workflow_pack_run_id": "packrun_exception_1"},
                    "result": {
                        "structured_output": {
                            "exception_summary_status": "REVIEW_REQUIRED",
                            "exception_count": 1,
                        }
                    },
                },
                "workflow_pack_run": {
                    "run_id": "packrun_exception_1",
                    "workflow_authority_owner": "lotus-manage",
                },
            },
        )
    )
    service = DpmCommandCenterService(  # type: ignore[arg-type]
        dpm_client=dpm_client,
        lotus_ai_client=ai_client,
    )

    response = await service.request_exception_summary(
        exception_id="me_source_1",
        request=DpmExceptionSummaryRequest(
            portfolio_id="PB_SG_GLOBAL_BAL_001",
            state="ACTIVE",
            requested_outputs=["exception_summary", "recommended_triage"],
            audience=["portfolio_manager", "operations"],
        ),
        correlation_id="corr-exception-summary-1",
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.manage_upstream_status == 200
    assert response.ai_upstream_status == 200
    assert response.exception_summary_request == {
        "requested_outputs": ["exception_summary", "recommended_triage"],
        "audience": ["portfolio_manager", "operations"],
    }
    assert response.exception_summary_input["portfolio_id"] == "PB_SG_GLOBAL_BAL_001"
    assert response.exception_summary_input["exception_count"] == 1
    assert response.exception_summary_input["redaction_policy"] == "NO_RAW_PAYLOADS"
    assert response.data["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"
    assert dpm_client.calls == [
        {
            "method": "list_exceptions",
            "params": {
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "mandate_id": None,
                "state": "ACTIVE",
                "limit": 200,
            },
            "correlation_id": "corr-exception-summary-1",
        }
    ]
    [ai_call] = ai_client.calls
    assert ai_call["pack_id"] == "dpm_exception_summary.pack"
    assert ai_call["workflow_surface"] == "dpm-exception-summary-ai-evidence"
    assert ai_call["correlation_id"] == "corr-exception-summary-1"
    task_request = ai_call["task_request"]
    assert task_request["caller"]["caller_app"] == "lotus-gateway"
    payload = task_request["context"]["payload"]
    assert payload["exception_summary_input"] == response.exception_summary_input
    assert payload["exception_summary_request"] == response.exception_summary_request
    assert payload["supportability"]["forbidden_actions"] == [
        "approve_rebalance",
        "contact_client",
        "invent_missing_evidence",
        "override_controls",
        "place_orders",
        "score_portfolio_manager",
    ]
    assert "lotus-manage:monitoring-exception:me_source_1" in task_request["context"]["source_refs"]


@pytest.mark.asyncio
async def test_dpm_command_center_exception_summary_preserves_ai_guardrail_failure() -> None:
    service = DpmCommandCenterService(  # type: ignore[arg-type]
        dpm_client=_FakeDpmClient((200, _exception_page())),
        lotus_ai_client=_FakeLotusAiClient(
            (
                422,
                {
                    "detail": (
                        "DPM_EXCEPTION_SUMMARY_GUARDRAIL_BLOCKED: "
                        "Forbidden exception summary outputs requested: client_message."
                    )
                },
            )
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_exception_summary(
            exception_id="me_source_1",
            request=DpmExceptionSummaryRequest(
                requested_outputs=["client_message"],
                audience=["pm"],
            ),
            correlation_id="corr-exception-summary-blocked",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["source_service"] == "lotus-ai"
    assert exc_info.value.detail["error_code"] == "AI_EXCEPTION_SUMMARY_UPSTREAM_ERROR"
    assert "DPM_EXCEPTION_SUMMARY_GUARDRAIL_BLOCKED" in exc_info.value.detail["detail"]


@pytest.mark.asyncio
async def test_dpm_command_center_exception_summary_missing_exception_is_product_safe() -> None:
    service = DpmCommandCenterService(  # type: ignore[arg-type]
        dpm_client=_FakeDpmClient((200, _exception_page())),
        lotus_ai_client=_FakeLotusAiClient((200, {})),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_exception_summary(
            exception_id="missing_exception",
            request=DpmExceptionSummaryRequest(),
            correlation_id="corr-exception-summary-missing",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["source_service"] == "lotus-manage"
    assert exc_info.value.detail["error_code"] == "MANAGE_MONITORING_EXCEPTION_NOT_FOUND"
    assert "missing_exception" in exc_info.value.detail["detail"]


def _outcome_ai_evidence() -> dict[str, object]:
    return {
        "contract_version": "1.0",
        "outcome_review_id": "or_1",
        "outcome_review_content_hash": "sha256:outcome-review-001",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "proof_pack_id": "pp_1",
        "permitted_use": "Draft support-only PM, CIO, compliance, and operations narratives.",
        "forbidden_actions": [
            "place_orders",
            "approve_rebalance",
            "override_controls",
            "invent_missing_evidence",
            "score_portfolio_manager",
            "contact_client",
        ],
        "forbidden_fields_removed": [],
        "overall_outcome": "Implemented rebalance stayed inside expected bands.",
        "dimensions": [{"dimension": "cash", "state": "MATCHED"}],
        "source_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "DPM_OUTCOME_AI_EVIDENCE_INPUT",
                "source_id": "or_1:dpm_outcome_ai_evidence_input",
                "content_hash": "sha256:outcome-ai-evidence-001",
            }
        ],
        "evidence_ref": {
            "source_system": "lotus-manage",
            "source_type": "DPM_OUTCOME_AI_EVIDENCE_INPUT",
            "source_id": "or_1:dpm_outcome_ai_evidence_input",
            "content_hash": "sha256:outcome-ai-evidence-001",
        },
        "client_communication_boundary": _client_communication_boundary(),
        "content_hash": "sha256:outcome-ai-evidence-001",
    }


def _client_communication_boundary() -> dict[str, object]:
    return {
        "boundary_id": "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY",
        "supportability_state": "BLOCKED",
        "source_system": "lotus-manage",
        "source_product_name": "DpmPostTradeOutcomeReview",
        "source_product_version": "v1",
        "client_communication_projected": False,
        "client_approval_projected": False,
        "reason_code": "OUTCOME_CLIENT_COMMUNICATION_NOT_SUPPORTED",
        "blocked_capabilities": [
            "client_approval",
            "client_contact",
            "client_message_generation",
            "communication_audit",
            "delivery_confirmation",
        ],
        "required_owner": "future client-communication owner",
        "required_source_product": "ClientCommunicationRecord:v1",
        "summary": (
            "Outcome review is internal-only until a client-communication owner publishes "
            "governed source events."
        ),
        "content_hash": "sha256:client-communication-boundary",
    }


def _pm_quality_score_run() -> dict[str, object]:
    return {
        "product_name": "PmOperatingQualityScoreRun",
        "product_version": "1.0",
        "score_run_id": "pmq_run_001",
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "portfolio_manager_id": "PM_SG_DPM_001",
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "as_of_date": "2026-05-16",
        "state": "READY",
        "score": "86.5",
        "reason_codes": ["PM_QUALITY_READY"],
        "indicator_results": [
            {
                "indicator_id": "source_evidence_completeness",
                "state": "READY",
                "score": "92.0",
                "reason_codes": ["PM_QUALITY_SOURCE_EVIDENCE_COMPLETE"],
                "source_refs": [
                    {
                        "source_system": "lotus-manage",
                        "source_type": "PmOperatingQualityScoreRun",
                        "source_id": "pmq_run_001",
                        "content_hash": "sha256:pmq-run-001",
                    }
                ],
            }
        ],
        "governance_evidence": {
            "approval_ref": "PMQ-APPROVAL-2026-05",
            "fairness_review_ref": "PMQ-FAIRNESS-2026-05",
        },
        "source_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "PmOperatingQualityScoreRun",
                "source_id": "pmq_run_001",
                "content_hash": "sha256:pmq-run-001",
            }
        ],
        "content_hash": "sha256:pmq-run-001",
        "forbidden_uses": [
            "compensation_decision",
            "hr_decision",
            "conduct_enforcement",
            "autonomous_pm_ranking",
        ],
    }


def _exception_page() -> dict[str, object]:
    return {
        "items": [
            {
                "exception_id": "me_source_1",
                "monitoring_run_id": "dmr_1",
                "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "detected_at": "2026-05-12T08:00:00Z",
                "as_of_date": "2026-05-12",
                "dimension": "SOURCE_READINESS",
                "severity": "HIGH",
                "reason_code": "SOURCE_READINESS_DEGRADED",
                "state": "ACTIVE",
                "recommended_action": "REVIEW_WITH_PM",
                "source_lineage": [
                    {
                        "source_system": "lotus-core",
                        "product_name": "DpmSourceReadiness",
                        "product_version": "v1",
                        "content_hash": "sha256:source-readiness",
                    }
                ],
            }
        ],
        "next_cursor": None,
    }
