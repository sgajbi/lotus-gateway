import pytest
from fastapi import HTTPException

from app.contracts.dpm_waves import DpmOperationsHandoffSummaryRequest, DpmWaveMemoRequest
from app.services.dpm_wave_service import DpmWaveService


class _FakeDpmClient:
    def __init__(self, result: tuple[int, dict]):
        self.result = result
        self.calls: list[dict[str, object]] = []

    async def create_wave(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "create_wave",
                "body": body,
                "idempotency_key": idempotency_key,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def simulate_wave(self, wave_id, body, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "simulate_wave",
                "wave_id": wave_id,
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_wave_supportability(self, wave_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "get_wave_supportability",
                "wave_id": wave_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_wave_report_input(self, wave_id, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "get_wave_report_input",
                "wave_id": wave_id,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def list_campaign_definitions(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "list_campaign_definitions",
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_campaign_definition(  # noqa: ANN001
        self, campaign_id, campaign_version, correlation_id
    ):
        self.calls.append(
            {
                "method": "get_campaign_definition",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def put_campaign_definition(  # noqa: ANN001
        self, campaign_id, campaign_version, body, correlation_id
    ):
        self.calls.append(
            {
                "method": "put_campaign_definition",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "body": body,
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
async def test_dpm_wave_service_preserves_manage_wave_truth_and_supportability() -> None:
    manage_payload = {
        "wave": {
            "wave_id": "dwv_001",
            "state": "HANDOFF_READY",
            "aggregate_metrics": {"item_count": 2, "ready_item_count": 2},
            "items": [
                {
                    "wave_item_id": "dwi_001",
                    "state": "HANDOFF_READY",
                    "proof_pack_id": "dpp_wave_001",
                }
            ],
        },
        "durable": True,
        "supportability": {
            "supportability_state": "ready",
            "reason": "wave_supportability_ready",
            "wave_id": "dwv_001",
            "wave_state": "HANDOFF_READY",
            "item_count": 2,
            "issues": [],
        },
    }
    client = _FakeDpmClient((201, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.create_wave(
        body={"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
        idempotency_key="wave-idem-1",
        correlation_id="corr-wave-create",
    )

    assert response.correlation_id == "corr-wave-create"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 201
    assert response.supportability.authority == "lotus-manage:RFC-0041"
    assert response.supportability.state == "ready"
    assert response.supportability.reason_codes == ["wave_supportability_ready"]
    assert response.supportability.wave_id == "dwv_001"
    assert response.supportability.wave_state == "HANDOFF_READY"
    assert response.supportability.item_count == 2
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "create_wave",
            "body": {"trigger_type": "EXPLICIT_PORTFOLIO_LIST"},
            "idempotency_key": "wave-idem-1",
            "correlation_id": "corr-wave-create",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_definition_payloads() -> None:
    manage_payload = {
        "campaign_id": "campaign-holdings-202605",
        "campaign_version": "2026.05",
        "product_name": "BulkReviewCampaignDefinition",
        "status": "ACTIVE",
        "content_hash": "sha256:campaign-definition",
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.put_campaign_definition(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        body={"status": "ACTIVE"},
        correlation_id="corr-campaign-definition",
    )

    assert response.correlation_id == "corr-campaign-definition"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "put_campaign_definition",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "body": {"status": "ACTIVE"},
            "correlation_id": "corr-campaign-definition",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_forwards_simulation_without_local_reconstruction() -> None:
    manage_payload = {
        "wave": {
            "wave_id": "dwv_001",
            "state": "PARTIALLY_SIMULATED",
            "items": [{"wave_item_id": "dwi_001", "state": "SIMULATION_BLOCKED"}],
        },
        "supportability": {
            "supportability_state": "degraded",
            "reason": "wave_degraded_items",
            "issues": [{"support_ref": "wave:dwv_001:item:1"}],
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.simulate_wave(
        wave_id="dwv_001",
        body={"actor_id": "pm_sg_1", "item_inputs": []},
        correlation_id="corr-wave-simulate",
    )

    assert response.supportability.state == "degraded"
    assert response.supportability.reason_codes == ["wave_degraded_items"]
    assert response.supportability.issue_count == 1
    assert response.data["wave"] == manage_payload["wave"]
    assert client.calls == [
        {
            "method": "simulate_wave",
            "wave_id": "dwv_001",
            "body": {"actor_id": "pm_sg_1", "item_inputs": []},
            "correlation_id": "corr-wave-simulate",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_manage_errors_are_product_safe() -> None:
    client = _FakeDpmClient(
        (
            422,
            {
                "detail": {
                    "code": "DPM_WAVE_INVALID_TRANSITION",
                    "message": "Wave dwv_001 cannot be approved from state DRAFT.",
                }
            },
        )
    )
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        await service.get_wave_supportability(
            wave_id="dwv_001",
            correlation_id="corr-wave-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-manage",
        "upstream_status": 422,
        "error_code": "MANAGE_WAVE_UPSTREAM_ERROR",
        "detail": (
            "DPM_WAVE_INVALID_TRANSITION: Wave dwv_001 cannot be approved from state DRAFT."
        ),
    }


@pytest.mark.asyncio
async def test_dpm_wave_service_exposes_manage_report_input_without_rebuilding() -> None:
    manage_payload = {
        "wave_id": "dwv_001",
        "report_input_ref": "report-input:dwv_001",
        "source_refs": ["lotus-manage:wave:dwv_001"],
        "supportability": {
            "supportability_state": "ready",
            "reason_codes": ["wave_report_input_ready"],
            "item_count": 1,
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_wave_report_input(
        wave_id="dwv_001",
        correlation_id="corr-wave-report-input",
    )

    assert response.supportability.state == "ready"
    assert response.supportability.reason_codes == ["wave_report_input_ready"]
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "get_wave_report_input",
            "wave_id": "dwv_001",
            "correlation_id": "corr-wave-report-input",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_pm_memo_uses_manage_report_input_and_lotus_ai_pack() -> None:
    manage_payload = {
        "wave_id": "dwv_001",
        "report_input_ref": "report-input:dwv_001",
        "source_refs": ["lotus-manage:source-check:dwv_001"],
        "supportability": {
            "supportability_state": "ready",
            "reason_codes": ["wave_report_input_ready"],
            "item_count": 1,
        },
    }
    ai_payload = {
        "run_id": "wf_run_wave_memo_001",
        "output": {"review_required": True, "memo_sections": ["PM summary"]},
    }
    dpm_client = _FakeDpmClient((200, manage_payload))
    ai_client = _FakeLotusAiClient((200, ai_payload))
    service = DpmWaveService(
        dpm_client=dpm_client,  # type: ignore[arg-type]
        lotus_ai_client=ai_client,  # type: ignore[arg-type]
    )

    response = await service.request_wave_pm_memo(
        wave_id="dwv_001",
        request=DpmWaveMemoRequest(
            requested_outputs=["wave_pm_memo", "approval_checklist"],
            audience=["portfolio_manager", "investment_control"],
        ),
        correlation_id="corr-wave-ai-memo",
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.manage_upstream_status == 200
    assert response.ai_upstream_status == 200
    assert response.wave_report_input == manage_payload
    assert response.memo_request == {
        "requested_outputs": ["wave_pm_memo", "approval_checklist"],
        "audience": ["portfolio_manager", "investment_control"],
    }
    assert response.data == ai_payload
    ai_call = ai_client.calls[0]
    assert ai_call["pack_id"] == "dpm_wave_pm_memo.pack"
    assert ai_call["version"] == "v1"
    assert ai_call["workflow_surface"] == "dpm-wave-ai-evidence"
    task_request = ai_call["task_request"]
    assert task_request["caller"] == {
        "caller_app": "lotus-gateway",
        "correlation_id": "corr-wave-ai-memo",
    }
    assert task_request["expected_output_label"] == "EXPLANATION_ONLY"
    payload = task_request["context"]["payload"]
    assert payload["wave_report_input"] == manage_payload
    assert payload["supportability"]["requires_human_review"] is True
    assert "place_orders" in payload["supportability"]["blocked_actions"]
    assert "place_orders" in payload["supportability"]["forbidden_actions"]
    assert "trade_approval" in payload["supportability"]["unsupported_claims"]
    assert task_request["context"]["source_refs"] == [
        "lotus-manage:source-check:dwv_001",
        "lotus-manage:wave-report-input:dwv_001",
        "lotus-manage:wave:dwv_001",
    ]


@pytest.mark.asyncio
async def test_dpm_wave_pm_memo_ai_errors_are_product_safe() -> None:
    dpm_client = _FakeDpmClient(
        (
            200,
            {
                "wave_id": "dwv_001",
                "supportability": {"supportability_state": "ready"},
            },
        )
    )
    service = DpmWaveService(
        dpm_client=dpm_client,  # type: ignore[arg-type]
        lotus_ai_client=_FakeLotusAiClient((503, {"detail": "workflow pack unavailable"})),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_wave_pm_memo(
            wave_id="dwv_001",
            request=DpmWaveMemoRequest(),
            correlation_id="corr-wave-ai-error",
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "source_service": "lotus-ai",
        "upstream_status": 503,
        "error_code": "AI_WAVE_PM_MEMO_UPSTREAM_ERROR",
        "detail": "workflow pack unavailable",
    }


@pytest.mark.asyncio
async def test_dpm_operations_handoff_summary_uses_manage_handoff_evidence_and_lotus_ai() -> None:
    manage_payload = _wave_report_input_with_handoff()
    ai_payload = {
        "run_id": "wf_run_operations_handoff_001",
        "output": {"review_required": True, "sections": ["Operations summary"]},
    }
    dpm_client = _FakeDpmClient((200, manage_payload))
    ai_client = _FakeLotusAiClient((200, ai_payload))
    service = DpmWaveService(
        dpm_client=dpm_client,  # type: ignore[arg-type]
        lotus_ai_client=ai_client,  # type: ignore[arg-type]
    )

    response = await service.request_operations_handoff_summary(
        wave_id="dwv_001",
        request=DpmOperationsHandoffSummaryRequest(
            requested_outputs=["operations_summary", "blocking_conditions"],
            audience=["operations", "portfolio_manager"],
        ),
        correlation_id="corr-operations-handoff-summary",
    )

    assert response.source_service == "lotus-ai"
    assert response.evidence_source_service == "lotus-manage"
    assert response.manage_upstream_status == 200
    assert response.ai_upstream_status == 200
    assert response.wave_report_input == manage_payload
    assert response.handoff_summary_request == {
        "requested_outputs": ["operations_summary", "blocking_conditions"],
        "audience": ["operations", "portfolio_manager"],
    }
    assert response.data == ai_payload
    assert dpm_client.calls == [
        {
            "method": "get_wave_report_input",
            "wave_id": "dwv_001",
            "correlation_id": "corr-operations-handoff-summary",
        }
    ]
    ai_call = ai_client.calls[0]
    assert ai_call["pack_id"] == "dpm_operations_handoff_summary.pack"
    assert ai_call["version"] == "v1"
    assert ai_call["workflow_surface"] == "dpm-operations-handoff-ai-evidence"
    task_request = ai_call["task_request"]
    assert task_request["caller"] == {
        "caller_app": "lotus-gateway",
        "correlation_id": "corr-operations-handoff-summary",
    }
    payload = task_request["context"]["payload"]
    assert payload["wave_report_input"] == manage_payload
    assert "memo_request" not in payload
    assert payload["handoff_summary_request"] == response.handoff_summary_request
    assert payload["supportability"]["requires_human_review"] is True
    assert "place_orders" in payload["supportability"]["forbidden_actions"]
    assert "order_routing" in payload["supportability"]["unsupported_claims"]
    assert task_request["context"]["source_refs"] == [
        "lotus-manage:handoff:handoff_001",
        "lotus-manage:wave-report-input:dwv_001",
        "lotus-manage:wave:dwv_001",
    ]


@pytest.mark.asyncio
async def test_dpm_operations_handoff_summary_ai_errors_are_product_safe() -> None:
    service = DpmWaveService(
        dpm_client=_FakeDpmClient((200, _wave_report_input_with_handoff())),  # type: ignore[arg-type]
        lotus_ai_client=_FakeLotusAiClient(
            (
                422,
                {
                    "detail": (
                        "OPERATIONS_HANDOFF_SUMMARY_GUARDRAIL_BLOCKED: "
                        "Forbidden operations handoff outputs requested: order_ticket."
                    )
                },
            )
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.request_operations_handoff_summary(
            wave_id="dwv_001",
            request=DpmOperationsHandoffSummaryRequest(requested_outputs=["order_ticket"]),
            correlation_id="corr-operations-handoff-error",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == {
        "source_service": "lotus-ai",
        "upstream_status": 422,
        "error_code": "AI_OPERATIONS_HANDOFF_SUMMARY_UPSTREAM_ERROR",
        "detail": (
            "OPERATIONS_HANDOFF_SUMMARY_GUARDRAIL_BLOCKED: "
            "Forbidden operations handoff outputs requested: order_ticket."
        ),
    }


def _wave_report_input_with_handoff() -> dict[str, object]:
    return {
        "contract_version": "1.0",
        "wave_id": "dwv_001",
        "wave_content_hash": "sha256:wave-content",
        "wave_state": "HANDOFF_READY",
        "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
        "trigger_id": "manual-wave-001",
        "trigger_rationale": "CIO model update for the Singapore balanced DPM book.",
        "as_of_date": "2026-05-12",
        "generated_at": "2026-05-12T08:00:00Z",
        "aggregate_metrics": {"item_count": 1, "handoff_ready_item_count": 1},
        "supportability": {
            "supportability_state": "ready",
            "reason_codes": ["wave_report_input_ready"],
            "item_count": 1,
        },
        "proof_pack_posture": {"ready_count": 1, "blocked_count": 0},
        "items": [
            {
                "wave_item_id": "dwi_001",
                "portfolio_id": "PB_SG_GLOBAL_BAL_001",
                "state": "HANDOFF_READY",
                "proof_pack_id": "dpp_wave_001",
            }
        ],
        "events": [{"event_type": "HANDOFF_READY", "event_time": "2026-05-12T08:00:00Z"}],
        "handoff_refs": [
            {
                "ref_type": "INTERNAL_OPERATIONS_HANDOFF",
                "ref_id": "handoff_001",
                "source_system": "lotus-manage",
                "content_hash": "sha256:handoff",
            }
        ],
        "source_refs": [
            "lotus-manage:wave:dwv_001",
            "lotus-manage:handoff:handoff_001",
        ],
        "redaction_policy": "NO_RAW_PAYLOADS",
        "external_execution_claimed": False,
        "evidence_ref": {
            "source_system": "lotus-manage",
            "source_type": "DPM_WAVE_REPORT_INPUT",
            "source_id": "dwv_001",
            "content_hash": "sha256:wave-report-input",
        },
        "content_hash": "sha256:wave-report-input",
        "report_input_ref": "report-input:dwv_001",
    }
