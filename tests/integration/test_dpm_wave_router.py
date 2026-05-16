from fastapi.testclient import TestClient

from app.main import app


def test_dpm_wave_preview_preserves_manage_supportability(monkeypatch) -> None:
    async def _fake_preview_wave(self, body, correlation_id):  # noqa: ANN001
        _ = self
        return 200, {
            "wave": {"wave_id": "dwv_preview_001", "state": "PREVIEWED"},
            "durable": False,
            "supportability": {
                "supportability_state": "ready",
                "reason": "wave_supportability_ready",
                "issue_counts": {"critical": 0, "warning": 0, "info": 1},
            },
        }

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.preview_wave", _fake_preview_wave)

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves/preview",
        json={
            "body": {
                "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
                "trigger_id": "manual-wave-20260503-001",
                "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            },
        },
        headers={"X-Correlation-Id": "corr-wave-router-preview"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supportability"]["state"] == "ready"
    assert payload["supportability"]["reason_codes"] == ["wave_supportability_ready"]
    assert payload["supportability"]["issue_count"] == 0
    assert payload["data"]["supportability"]["supportability_state"] == "ready"


def test_dpm_wave_create_forwards_body_and_idempotency_key(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_create_wave(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["idempotency_key"] = idempotency_key
        captured["correlation_id"] = correlation_id
        return 201, {
            "wave": {"wave_id": "dwv_001", "state": "PREVIEWED"},
            "durable": True,
            "supportability": {
                "supportability_state": "ready",
                "reason": "wave_supportability_ready",
            },
        }

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.create_wave", _fake_create_wave)

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves",
        json={
            "idempotency_key": "wave-idem-1",
            "body": {
                "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
                "trigger_id": "manual-wave-20260503-001",
                "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
            },
        },
        headers={"X-Correlation-Id": "corr-wave-router-create"},
    )

    assert response.status_code == 200
    assert captured == {
        "body": {
            "trigger_type": "EXPLICIT_PORTFOLIO_LIST",
            "trigger_id": "manual-wave-20260503-001",
            "portfolios": [{"portfolio_id": "PB_SG_GLOBAL_BAL_001"}],
        },
        "idempotency_key": "wave-idem-1",
        "correlation_id": "corr-wave-router-create",
    }
    payload = response.json()
    assert payload["supportability"]["state"] == "ready"
    assert payload["data"]["wave"]["wave_id"] == "dwv_001"


def test_dpm_wave_list_passes_filters_without_reconstructing_state(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_list_waves(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {
            "items": [
                {
                    "wave_id": "dwv_001",
                    "wave_state": "HANDOFF_READY",
                    "supportability_state": "ready",
                }
            ],
            "limit": 25,
            "offset": 0,
            "returned_count": 1,
        }

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_waves", _fake_list_waves)

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/waves"
        "?state=HANDOFF_READY&supportability_state=ready&limit=25&offset=0",
        headers={"X-Correlation-Id": "corr-wave-router-list"},
    )

    assert response.status_code == 200
    assert captured == {
        "params": {
            "state": "HANDOFF_READY",
            "trigger_type": None,
            "as_of_date": None,
            "supportability_state": "ready",
            "limit": 25,
            "offset": 0,
        },
        "correlation_id": "corr-wave-router-list",
    }
    assert response.json()["data"]["items"][0]["wave_state"] == "HANDOFF_READY"


def test_campaign_definition_routes_preserve_manage_payloads(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_put_campaign_definition(  # noqa: ANN001
        self, campaign_id, campaign_version, body, correlation_id
    ):
        _ = self
        captured["put"] = {
            "campaign_id": campaign_id,
            "campaign_version": campaign_version,
            "body": body,
            "correlation_id": correlation_id,
        }
        return 200, {
            "campaign_id": campaign_id,
            "campaign_version": campaign_version,
            "product_name": "BulkReviewCampaignDefinition",
            "status": body["status"],
            "content_hash": "sha256:campaign-definition",
        }

    async def _fake_list_campaign_definitions(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["list"] = {"params": params, "correlation_id": correlation_id}
        return 200, {
            "items": [
                {
                    "campaign_id": "campaign-holdings-202605",
                    "campaign_version": "2026.05",
                    "product_name": "BulkReviewCampaignDefinition",
                }
            ],
            "limit": params["limit"],
            "offset": params["offset"],
            "count": 1,
        }

    async def _fake_get_campaign_definition(  # noqa: ANN001
        self, campaign_id, campaign_version, correlation_id
    ):
        _ = self
        captured["get"] = {
            "campaign_id": campaign_id,
            "campaign_version": campaign_version,
            "correlation_id": correlation_id,
        }
        return 200, {
            "campaign_id": campaign_id,
            "campaign_version": campaign_version,
            "product_name": "BulkReviewCampaignDefinition",
            "status": "ACTIVE",
        }

    async def _fake_get_campaign_definition_lifecycle_events(  # noqa: ANN001
        self, campaign_id, campaign_version, correlation_id
    ):
        _ = self
        captured["lifecycle_events"] = {
            "campaign_id": campaign_id,
            "campaign_version": campaign_version,
            "correlation_id": correlation_id,
        }
        return 200, {
            "campaign_id": campaign_id,
            "campaign_version": campaign_version,
            "events": [
                {
                    "event_type": "CAMPAIGN_DEFINITION_CREATED",
                    "actor_id": "pm_sg_1",
                    "source_service": "lotus-manage",
                }
            ],
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.put_campaign_definition",
        _fake_put_campaign_definition,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_campaign_definitions",
        _fake_list_campaign_definitions,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_campaign_definition",
        _fake_get_campaign_definition,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_campaign_definition_lifecycle_events",
        _fake_get_campaign_definition_lifecycle_events,
    )

    client = TestClient(app)
    put_response = client.put(
        "/api/v1/dpm/command-center/waves/campaign-definitions/"
        "campaign-holdings-202605/versions/2026.05",
        json={"body": {"status": "ACTIVE", "candidates": []}},
        headers={"X-Correlation-Id": "corr-campaign-put"},
    )
    list_response = client.get(
        "/api/v1/dpm/command-center/waves/campaign-definitions"
        "?campaign_status=ACTIVE&limit=25&offset=0",
        headers={"X-Correlation-Id": "corr-campaign-list"},
    )
    get_response = client.get(
        "/api/v1/dpm/command-center/waves/campaign-definitions/"
        "campaign-holdings-202605/versions/2026.05",
        headers={"X-Correlation-Id": "corr-campaign-get"},
    )
    lifecycle_events_response = client.get(
        "/api/v1/dpm/command-center/waves/campaign-definitions/"
        "campaign-holdings-202605/versions/2026.05/lifecycle-events",
        headers={"X-Correlation-Id": "corr-campaign-lifecycle"},
    )

    assert put_response.status_code == 200
    assert put_response.json()["data"]["product_name"] == "BulkReviewCampaignDefinition"
    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["campaign_id"] == "campaign-holdings-202605"
    assert get_response.status_code == 200
    assert get_response.json()["data"]["campaign_version"] == "2026.05"
    assert lifecycle_events_response.status_code == 200
    assert (
        lifecycle_events_response.json()["data"]["events"][0]["event_type"]
        == "CAMPAIGN_DEFINITION_CREATED"
    )
    assert captured == {
        "put": {
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "body": {"status": "ACTIVE", "candidates": []},
            "correlation_id": "corr-campaign-put",
        },
        "list": {
            "params": {
                "campaign_id": None,
                "campaign_status": "ACTIVE",
                "as_of_date": None,
                "limit": 25,
                "offset": 0,
            },
            "correlation_id": "corr-campaign-list",
        },
        "get": {
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "correlation_id": "corr-campaign-get",
        },
        "lifecycle_events": {
            "campaign_id": "campaign-holdings-202605",
            "campaign_version": "2026.05",
            "correlation_id": "corr-campaign-lifecycle",
        },
    }


def test_dpm_wave_actions_preserve_manage_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_select_wave_item(self, wave_id, wave_item_id, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["wave_id"] = wave_id
        captured["wave_item_id"] = wave_item_id
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "wave": {
                "wave_id": wave_id,
                "state": "SIMULATED",
                "items": [
                    {
                        "wave_item_id": wave_item_id,
                        "selected_alternative_id": body["alternative_id"],
                        "proof_pack_id": "dpp_wave_001",
                    }
                ],
            },
            "supportability": {"supportability_state": "ready"},
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.select_wave_item",
        _fake_select_wave_item,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves/dwv_001/items/dwi_001/select",
        json={
            "body": {
                "alternative_id": "alt_001",
                "actor_id": "pm_sg_1",
                "reason_code": "PM_SELECTED",
                "generate_proof_pack": True,
            }
        },
        headers={"X-Correlation-Id": "corr-wave-router-select"},
    )

    assert response.status_code == 200
    assert captured == {
        "wave_id": "dwv_001",
        "wave_item_id": "dwi_001",
        "body": {
            "alternative_id": "alt_001",
            "actor_id": "pm_sg_1",
            "reason_code": "PM_SELECTED",
            "generate_proof_pack": True,
        },
        "correlation_id": "corr-wave-router-select",
    }
    assert response.json()["data"]["wave"]["items"][0]["proof_pack_id"] == "dpp_wave_001"


def test_dpm_wave_error_is_not_marked_ready(monkeypatch) -> None:
    async def _fake_get_wave(self, wave_id, correlation_id):  # noqa: ANN001
        _ = self, wave_id, correlation_id
        return 404, {"detail": "Wave dwv_missing was not found."}

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_wave", _fake_get_wave)

    client = TestClient(app)
    response = client.get("/api/v1/dpm/command-center/waves/dwv_missing")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "MANAGE_WAVE_UPSTREAM_ERROR"
    assert response.json()["detail"]["detail"] == "Wave dwv_missing was not found."


def test_dpm_wave_report_input_preserves_manage_evidence(monkeypatch) -> None:
    async def _fake_get_wave_report_input(self, wave_id, correlation_id):  # noqa: ANN001
        _ = self
        return 200, {
            "wave_id": wave_id,
            "report_input_ref": f"report-input:{wave_id}",
            "source_refs": [f"lotus-manage:wave:{wave_id}"],
            "supportability": {
                "supportability_state": "ready",
                "reason_codes": ["wave_report_input_ready"],
            },
            "correlation_id": correlation_id,
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_wave_report_input",
        _fake_get_wave_report_input,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/waves/dwv_001/report-input",
        headers={"X-Correlation-Id": "corr-wave-router-report-input"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supportability"]["state"] == "ready"
    assert payload["data"]["report_input_ref"] == "report-input:dwv_001"
    assert payload["data"]["correlation_id"] == "corr-wave-router-report-input"


def test_dpm_wave_ai_pm_memo_uses_lotus_ai_workflow_pack(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_wave_report_input(self, wave_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["manage_wave_id"] = wave_id
        captured["manage_correlation_id"] = correlation_id
        return 200, {
            "wave_id": wave_id,
            "report_input_ref": f"report-input:{wave_id}",
            "source_refs": [f"lotus-manage:wave:{wave_id}"],
            "supportability": {
                "supportability_state": "ready",
                "reason_codes": ["wave_report_input_ready"],
            },
        }

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN001, ANN003
        _ = self
        captured["ai_kwargs"] = kwargs
        return 200, {"run_id": "wf_run_wave_memo_001", "status": "REVIEW_REQUIRED"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_wave_report_input",
        _fake_get_wave_report_input,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves/dwv_001/ai-pm-memo",
        json={
            "requested_outputs": ["wave_pm_memo", "approval_checklist"],
            "audience": ["portfolio_manager", "investment_control"],
        },
        headers={"X-Correlation-Id": "corr-wave-router-ai-memo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_service"] == "lotus-ai"
    assert payload["evidence_source_service"] == "lotus-manage"
    assert payload["wave_report_input"]["report_input_ref"] == "report-input:dwv_001"
    assert payload["memo_request"]["requested_outputs"] == [
        "wave_pm_memo",
        "approval_checklist",
    ]
    ai_kwargs = captured["ai_kwargs"]
    assert ai_kwargs["pack_id"] == "dpm_wave_pm_memo.pack"
    assert ai_kwargs["workflow_surface"] == "dpm-wave-ai-evidence"
    assert ai_kwargs["correlation_id"] == "corr-wave-router-ai-memo"
    assert ai_kwargs["task_request"]["caller"]["caller_app"] == "lotus-gateway"
    supportability = ai_kwargs["task_request"]["context"]["payload"]["supportability"]
    assert supportability["requires_human_review"] is True
    assert "approve_rebalance" in supportability["blocked_actions"]


def test_dpm_wave_operations_handoff_summary_uses_lotus_ai_workflow_pack(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_wave_report_input(self, wave_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["manage_wave_id"] = wave_id
        captured["manage_correlation_id"] = correlation_id
        return 200, _wave_report_input_with_handoff(wave_id)

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN001, ANN003
        _ = self
        captured["ai_kwargs"] = kwargs
        return 200, {"run_id": "wf_run_handoff_001", "status": "REVIEW_REQUIRED"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_wave_report_input",
        _fake_get_wave_report_input,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/waves/dwv_001/operations-handoff-summary",
        json={
            "requested_outputs": ["operations_summary", "blocking_conditions"],
            "audience": ["operations", "portfolio_manager"],
        },
        headers={"X-Correlation-Id": "corr-wave-router-handoff-summary"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_service"] == "lotus-ai"
    assert payload["evidence_source_service"] == "lotus-manage"
    assert payload["wave_report_input"]["handoff_refs"][0]["ref_id"] == "handoff_001"
    assert payload["handoff_summary_request"]["requested_outputs"] == [
        "operations_summary",
        "blocking_conditions",
    ]
    ai_kwargs = captured["ai_kwargs"]
    assert ai_kwargs["pack_id"] == "dpm_operations_handoff_summary.pack"
    assert ai_kwargs["workflow_surface"] == "dpm-operations-handoff-ai-evidence"
    assert ai_kwargs["correlation_id"] == "corr-wave-router-handoff-summary"
    assert ai_kwargs["task_request"]["caller"]["caller_app"] == "lotus-gateway"
    supportability = ai_kwargs["task_request"]["context"]["payload"]["supportability"]
    assert supportability["requires_human_review"] is True
    assert "approve_rebalance" in supportability["forbidden_actions"]
    assert "order_routing" in supportability["unsupported_claims"]
    assert "memo_request" not in ai_kwargs["task_request"]["context"]["payload"]


def _wave_report_input_with_handoff(wave_id: str) -> dict[str, object]:
    return {
        "contract_version": "1.0",
        "wave_id": wave_id,
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
            f"lotus-manage:wave:{wave_id}",
            "lotus-manage:handoff:handoff_001",
        ],
        "redaction_policy": "NO_RAW_PAYLOADS",
        "external_execution_claimed": False,
        "evidence_ref": {
            "source_system": "lotus-manage",
            "source_type": "DPM_WAVE_REPORT_INPUT",
            "source_id": wave_id,
            "content_hash": "sha256:wave-report-input",
        },
        "content_hash": "sha256:wave-report-input",
        "report_input_ref": f"report-input:{wave_id}",
    }
