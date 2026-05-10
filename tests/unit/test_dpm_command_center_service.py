import pytest
from fastapi import HTTPException

from app.contracts.dpm_command_center import DpmOutcomeReviewNarrativeRequest
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
        "event_count": 4,
        "supportability_state": "READY",
        "event_type_counts": {
            "PROOF_PACK_CREATED": 1,
            "WAVE_HANDOFF_READY": 1,
            "OUTCOME_REVIEW_CREATED": 1,
            "OUTCOME_REVIEW_EVENT": 1,
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
    assert response.supportability.event_count == 4
    assert response.supportability.event_type_counts["WAVE_HANDOFF_READY"] == 1
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
        "content_hash": "sha256:outcome-ai-evidence-001",
    }
