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

    async def get_campaign_definition_lifecycle_events(  # noqa: ANN001
        self, campaign_id, campaign_version, correlation_id
    ):
        self.calls.append(
            {
                "method": "get_campaign_definition_lifecycle_events",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_campaign_definition_preview_readiness(  # noqa: ANN001
        self, campaign_id, campaign_version, params, correlation_id
    ):
        self.calls.append(
            {
                "method": "get_campaign_definition_preview_readiness",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_campaign_definition_launch_history(  # noqa: ANN001
        self, campaign_id, campaign_version, params, correlation_id
    ):
        self.calls.append(
            {
                "method": "get_campaign_definition_launch_history",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_campaign_definition_launch_package(  # noqa: ANN001
        self, campaign_id, campaign_version, params, correlation_id
    ):
        self.calls.append(
            {
                "method": "get_campaign_definition_launch_package",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def launch_campaign_definition(  # noqa: ANN001
        self, campaign_id, campaign_version, body, correlation_id
    ):
        self.calls.append(
            {
                "method": "launch_campaign_definition",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def discover_campaigns(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "discover_campaigns",
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def get_campaign_operating_queue(self, params, correlation_id):  # noqa: ANN001
        self.calls.append(
            {
                "method": "get_campaign_operating_queue",
                "params": params,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def create_campaign_assignment_task(  # noqa: ANN001
        self, campaign_id, campaign_version, body, correlation_id
    ):
        self.calls.append(
            {
                "method": "create_campaign_assignment_task",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "body": body,
                "correlation_id": correlation_id,
            }
        )
        return self.result

    async def transition_campaign_assignment_task(  # noqa: ANN001
        self, campaign_id, campaign_version, task_ref, body, correlation_id
    ):
        self.calls.append(
            {
                "method": "transition_campaign_assignment_task",
                "campaign_id": campaign_id,
                "campaign_version": campaign_version,
                "task_ref": task_ref,
                "body": body,
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
async def test_dpm_wave_service_preserves_campaign_lifecycle_events() -> None:
    manage_payload = {
        "campaign_id": "campaign-holdings-202605",
        "campaign_version": "2026.05",
        "events": [
            {
                "event_type": "LAUNCHED",
                "actor_id": "pm_sg_1",
                "occurred_at": "2026-05-14T09:30:00Z",
                "source_service": "lotus-manage",
                "wave_id": "dwv_campaign_launch_001",
                "requested_as_of_date": "2026-05-10",
                "correlation_id": "corr-campaign-launch",
                "idempotency_key": "campaign-launch:campaign-holdings-202605:2026.05:abc",
            }
        ],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_campaign_definition_lifecycle_events(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        correlation_id="corr-campaign-lifecycle",
    )

    assert response.correlation_id == "corr-campaign-lifecycle"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "get_campaign_definition_lifecycle_events",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "correlation_id": "corr-campaign-lifecycle",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_preview_readiness_payload() -> None:
    manage_payload = {
        "product_name": "BulkReviewCampaignDefinitionPreviewReadiness",
        "product_version": "v1",
        "campaign_id": "campaign-holdings-202605",
        "campaign_version": "2026.05",
        "requested_as_of_date": "2026-05-10",
        "actor_id": "pm_sg_1",
        "supportability_state": "BLOCKED",
        "reason_codes": ["campaign_definition_actor_not_entitled"],
        "blocked_actions": ["preview_wave", "create_wave"],
        "source_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "BulkReviewCampaignDefinition",
                "source_id": "campaign-holdings-202605:2026.05",
                "content_hash": "sha256:campaign-definition",
            }
        ],
        "operating_boundaries": [
            "NO_MEMBERSHIP_RECALCULATION",
            "NO_ORDER_GENERATION",
            "NO_OMS_EXECUTION_CLAIM",
        ],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_campaign_definition_preview_readiness(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        filters={"requested_as_of_date": "2026-05-10", "actor_id": "pm_sg_1"},
        correlation_id="corr-campaign-preview-readiness",
    )

    assert response.correlation_id == "corr-campaign-preview-readiness"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.data == manage_payload
    assert response.data["supportability_state"] == "BLOCKED"
    assert response.data["reason_codes"] == ["campaign_definition_actor_not_entitled"]
    assert response.data["operating_boundaries"] == manage_payload["operating_boundaries"]
    assert client.calls == [
        {
            "method": "get_campaign_definition_preview_readiness",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "params": {"requested_as_of_date": "2026-05-10", "actor_id": "pm_sg_1"},
            "correlation_id": "corr-campaign-preview-readiness",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_launch_history_payload() -> None:
    manage_payload = {
        "product_name": "BulkReviewCampaignDefinitionLaunchHistory",
        "product_version": "v1",
        "campaign_id": "campaign-holdings-202605",
        "campaign_version": "2026.05",
        "items": [
            {
                "wave_id": "dwv_campaign_launch_001",
                "launched_at": "2026-05-10T00:00:00Z",
                "launched_by": "pm_sg_1",
                "requested_as_of_date": "2026-05-10",
                "correlation_id": "corr-campaign-launch",
                "idempotency_key": "campaign-launch:campaign-holdings-202605:2026.05:abc",
            }
        ],
        "limit": 25,
        "offset": 0,
        "count": 1,
        "total_count": 1,
        "operating_boundaries": [
            "NO_MAKER_CHECKER_WORKFLOW",
            "NO_TRADE_APPROVAL",
            "NO_ORDER_GENERATION",
            "NO_OMS_EXECUTION_CLAIM",
        ],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_campaign_definition_launch_history(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        filters={"limit": 25, "offset": 0},
        correlation_id="corr-campaign-launch-history",
    )

    assert response.correlation_id == "corr-campaign-launch-history"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.data == manage_payload
    assert response.data["items"][0]["idempotency_key"] == (
        "campaign-launch:campaign-holdings-202605:2026.05:abc"
    )
    assert response.data["items"][0]["launched_by"] == "pm_sg_1"
    assert response.data["total_count"] == 1
    assert response.data["operating_boundaries"] == manage_payload["operating_boundaries"]
    assert client.calls == [
        {
            "method": "get_campaign_definition_launch_history",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "params": {"limit": 25, "offset": 0},
            "correlation_id": "corr-campaign-launch-history",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_launch_package_payload() -> None:
    manage_payload = {
        "product_name": "BulkReviewCampaignDefinitionLaunchPackage",
        "campaign_id": "campaign-holdings-202605",
        "campaign_version": "2026.05",
        "launch_state": "READY",
        "reason_codes": [],
        "create_headers": {
            "Idempotency-Key": "campaign-launch:campaign-holdings-202605:2026.05:abc",
            "X-Correlation-Id": "corr-campaign-launch",
        },
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_campaign_definition_launch_package(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        filters={
            "requested_as_of_date": "2026-05-10",
            "actor_id": "pm_sg_1",
            "correlation_id": "corr-campaign-launch",
        },
        correlation_id="corr-gateway",
    )

    assert response.correlation_id == "corr-gateway"
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "get_campaign_definition_launch_package",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "params": {
                "requested_as_of_date": "2026-05-10",
                "actor_id": "pm_sg_1",
                "correlation_id": "corr-campaign-launch",
            },
            "correlation_id": "corr-gateway",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_launch_wave_truth() -> None:
    manage_payload = {
        "wave": {
            "wave_id": "dwv_campaign_launch_001",
            "state": "CREATED",
            "trigger_type": "BULK_REVIEW_CAMPAIGN",
        },
        "durable": True,
        "idempotent_replay": True,
        "supportability": {
            "supportability_state": "ready",
            "reason_codes": ["campaign_definition_launch_replayed"],
        },
    }
    body = {
        "requested_as_of_date": "2026-05-10",
        "actor_id": "pm_sg_1",
        "correlation_id": "corr-campaign-launch",
    }
    client = _FakeDpmClient((201, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.launch_campaign_definition(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        body=body,
        correlation_id="corr-gateway",
    )

    assert response.upstream_status == 201
    assert response.supportability.state == "ready"
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "launch_campaign_definition",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "body": body,
            "correlation_id": "corr-gateway",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_discovery_payload() -> None:
    manage_payload = {
        "items": [
            {
                "product_name": "BulkReviewCampaignDiscovery",
                "product_version": "v1",
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "campaign_status": "ACTIVE",
                "candidate_count": 12,
                "eligible_candidate_count": 10,
                "content_hash": "sha256:campaign-discovery",
            }
        ],
        "limit": 25,
        "offset": 0,
        "count": 1,
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.discover_campaigns(
        filters={
            "campaign_status": "ACTIVE",
            "active_on": "2026-05-16",
            "include_expired": False,
            "limit": 25,
            "offset": 0,
        },
        correlation_id="corr-campaign-discovery",
    )

    assert response.correlation_id == "corr-campaign-discovery"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.data == manage_payload
    assert client.calls == [
        {
            "method": "discover_campaigns",
            "params": {
                "campaign_status": "ACTIVE",
                "active_on": "2026-05-16",
                "include_expired": False,
                "limit": 25,
                "offset": 0,
            },
            "correlation_id": "corr-campaign-discovery",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_workflow_queue_payload() -> None:
    manage_payload = {
        "product_name": "BulkReviewCampaignOperatingQueue",
        "product_version": "v1",
        "items": [
            {
                "campaign_id": "campaign-holdings-202605",
                "campaign_version": "2026.05",
                "task_ref": "task-review-001",
                "supportability_state": "READY",
                "source_refs": [{"source_system": "lotus-manage"}],
                "content_hash": "sha256:operating-queue",
            }
        ],
        "count": 1,
        "limit": 25,
        "offset": 0,
        "operating_boundaries": [
            "NO_ORDER_GENERATION",
            "NO_OMS_EXECUTION_CLAIM",
            "NO_EXTERNAL_WORKFLOW_ORCHESTRATION",
        ],
    }
    client = _FakeDpmClient((200, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.get_campaign_operating_queue(
        filters={"campaign_status": "ACTIVE", "limit": 25, "offset": 0},
        correlation_id="corr-campaign-operating-queue",
    )

    assert response.correlation_id == "corr-campaign-operating-queue"
    assert response.source_service == "lotus-manage"
    assert response.upstream_status == 200
    assert response.data == manage_payload
    assert response.data["items"][0]["content_hash"] == "sha256:operating-queue"
    assert "NO_OMS_EXECUTION_CLAIM" in response.data["operating_boundaries"]
    assert client.calls == [
        {
            "method": "get_campaign_operating_queue",
            "params": {"campaign_status": "ACTIVE", "limit": 25, "offset": 0},
            "correlation_id": "corr-campaign-operating-queue",
        }
    ]


@pytest.mark.asyncio
async def test_dpm_wave_service_preserves_campaign_assignment_task_transition_payload() -> None:
    manage_payload = {
        "product_name": "BulkReviewCampaignAssignmentTaskTransition",
        "product_version": "v1",
        "campaign_id": "campaign-holdings-202605",
        "campaign_version": "2026.05",
        "task_ref": "task-review-001",
        "transition_type": "MARK_SUPPORTABLE",
        "from_status": "READY_FOR_REVIEW",
        "to_status": "SUPPORTABLE",
        "reason_codes": ["campaign_assignment_task_transition_recorded"],
        "source_refs": [{"source_system": "lotus-manage"}],
        "content_hash": "sha256:task-transition",
        "operating_boundaries": [
            "NO_ORDER_GENERATION",
            "NO_OMS_EXECUTION_CLAIM",
            "NO_CLIENT_CONTACT_WORKFLOW",
        ],
    }
    body = {
        "transition_type": "MARK_SUPPORTABLE",
        "actor_id": "pm_sg_1",
        "reason_code": "campaign_assignment_task_transition_recorded",
    }
    client = _FakeDpmClient((201, manage_payload))
    service = DpmWaveService(dpm_client=client)  # type: ignore[arg-type]

    response = await service.transition_campaign_assignment_task(
        campaign_id="campaign-holdings-202605",
        campaign_version="2026.05",
        task_ref="task-review-001",
        body=body,
        correlation_id="corr-campaign-task-transition",
    )

    assert response.upstream_status == 201
    assert response.data == manage_payload
    assert response.data["from_status"] == "READY_FOR_REVIEW"
    assert response.data["to_status"] == "SUPPORTABLE"
    assert "NO_CLIENT_CONTACT_WORKFLOW" in response.data["operating_boundaries"]
    assert client.calls == [
        {
            "method": "transition_campaign_assignment_task",
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "task_ref": "task-review-001",
            "body": body,
            "correlation_id": "corr-campaign-task-transition",
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
