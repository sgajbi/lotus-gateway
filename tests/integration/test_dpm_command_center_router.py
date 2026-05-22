from fastapi.testclient import TestClient

from app.main import app


def test_dpm_command_center_summary_passes_filters_and_preserves_manage_truth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_command_center(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {
            "health_distribution": {"READY": 3, "PENDING_REVIEW": 1},
            "evaluated_mandates": 4,
            "active_exception_count": 1,
            "supportability": {
                "data_completeness_state": "PARTIAL",
                "partial_readiness_reasons": ["PM_BOOK_DISCOVERY_NOT_AVAILABLE"],
                "source_run_id": "dmr_1",
            },
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_command_center",
        _fake_get_command_center,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center"
        "?tenant_id=default&portfolio_manager_id=PM_SG_DPM_001"
        "&book_id=BOOK_SG_BALANCED_DPM&health_state=PENDING_REVIEW&limit=25",
        headers={"X-Correlation-Id": "corr-command-router-1"},
    )

    assert response.status_code == 200
    assert captured == {
        "params": {
            "portfolio_manager_id": "PM_SG_DPM_001",
            "tenant_id": "default",
            "as_of_date": None,
            "book_id": "BOOK_SG_BALANCED_DPM",
            "health_state": "PENDING_REVIEW",
            "limit": 25,
        },
        "correlation_id": "corr-command-router-1",
    }
    payload = response.json()
    assert payload["supportability"]["state"] == "PARTIAL"
    assert payload["supportability"]["source_run_id"] == "dmr_1"
    assert payload["data"]["health_distribution"] == {"READY": 3, "PENDING_REVIEW": 1}


def test_dpm_command_center_monitoring_run_action_forwards_body(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_run_monitoring_once(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "monitoring_run_id": "dmr_1",
            "status": "SUCCEEDED",
            "mandate_results": [{"mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001"}],
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.run_monitoring_once",
        _fake_run_monitoring_once,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/monitoring/run-once",
        json={
            "body": {
                "mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"],
                "as_of_date": "2026-05-03",
                "tenant_id": "default",
                "portfolio_manager_id": "PM_SG_DPM_001",
            }
        },
        headers={"X-Correlation-Id": "corr-command-router-run"},
    )

    assert response.status_code == 200
    assert captured == {
        "body": {
            "mandate_ids": ["MANDATE_PB_SG_GLOBAL_BAL_001"],
            "as_of_date": "2026-05-03",
            "tenant_id": "default",
            "portfolio_manager_id": "PM_SG_DPM_001",
        },
        "correlation_id": "corr-command-router-run",
    }
    assert response.json()["data"]["monitoring_run_id"] == "dmr_1"


def test_dpm_command_center_exception_resolution_forwards_reason(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_resolve_monitoring_exception(
        self,
        exception_id,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["exception_id"] = exception_id
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "exception_id": exception_id,
            "state": "RESOLVED",
            "resolution_reason": body["resolution_reason"],
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.resolve_monitoring_exception",
        _fake_resolve_monitoring_exception,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/exceptions/me_source_1/resolve",
        json={"resolution_reason": "SOURCE_DATA_REPAIRED_AND_RECALCULATED"},
        headers={"X-Correlation-Id": "corr-command-router-resolve"},
    )

    assert response.status_code == 200
    assert captured == {
        "exception_id": "me_source_1",
        "body": {"resolution_reason": "SOURCE_DATA_REPAIRED_AND_RECALCULATED"},
        "correlation_id": "corr-command-router-resolve",
    }
    assert response.json()["data"]["state"] == "RESOLVED"


def test_dpm_command_center_mandate_health_drilldown_preserves_dimensions(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_mandate_health(self, mandate_id, correlation_id):  # noqa: ANN001
        _ = self
        captured["mandate_id"] = mandate_id
        captured["correlation_id"] = correlation_id
        return 200, {
            "health_snapshot_id": "mh_1",
            "mandate_id": mandate_id,
            "health_score": 97,
            "dimension_scores": [{"dimension": "SOURCE_READINESS", "state": "READY"}],
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_mandate_health",
        _fake_get_mandate_health,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/mandates/MANDATE_PB_SG_GLOBAL_BAL_001/health",
        headers={"X-Correlation-Id": "corr-command-router-health"},
    )

    assert response.status_code == 200
    assert captured == {
        "mandate_id": "MANDATE_PB_SG_GLOBAL_BAL_001",
        "correlation_id": "corr-command-router-health",
    }
    assert response.json()["data"]["dimension_scores"] == [
        {"dimension": "SOURCE_READINESS", "state": "READY"}
    ]


def test_dpm_command_center_portfolio_memory_passes_limit_and_preserves_events(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_portfolio_memory(
        self,
        portfolio_id,
        params,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["portfolio_id"] = portfolio_id
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {
            "portfolio_id": portfolio_id,
            "event_count": 3,
            "supportability_state": "READY",
            "event_type_counts": {
                "PROOF_PACK_CREATED": 1,
                "OUTCOME_REVIEW_CREATED": 1,
                "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION": 1,
            },
            "source_systems": ["lotus-manage", "lotus-core"],
            "reason_codes": ["SOURCE_READY"],
            "content_hash": "sha256:portfolio-memory",
            "events": [
                {"event_id": "memory:proof-pack:dpp_1", "event_type": "PROOF_PACK_CREATED"},
                {"event_id": "memory:outcome-review:or_1", "event_type": "OUTCOME_REVIEW_CREATED"},
                {
                    "event_id": "memory:campaign-assignment-task-transition:transition_001",
                    "event_type": "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION",
                    "source_refs": [
                        {"source_system": "lotus-manage", "source_id": "campaign_001:v1"}
                    ],
                    "artifact_refs": [{"source_system": "lotus-manage", "source_id": "task_001"}],
                    "content_hash": "sha256:assignment-task-transition",
                    "reason_codes": ["BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION_RECORDED"],
                    "metadata": {
                        "task_ref": "task-ref-001",
                        "transition_type": "ACKNOWLEDGE",
                        "from_status": "OPEN",
                        "to_status": "IN_PROGRESS",
                        "sla_posture": "ON_TRACK",
                    },
                },
            ],
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_portfolio_memory",
        _fake_get_portfolio_memory,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/portfolios/PB_SG_GLOBAL_BAL_001/memory?limit=20",
        headers={"X-Correlation-Id": "corr-portfolio-memory-router"},
    )

    assert response.status_code == 200
    assert captured == {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001",
        "params": {"limit": 20},
        "correlation_id": "corr-portfolio-memory-router",
    }
    payload = response.json()
    assert payload["supportability"]["state"] == "READY"
    assert payload["supportability"]["event_count"] == 3
    assert (
        payload["supportability"]["event_type_counts"][
            "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION"
        ]
        == 1
    )
    assert payload["supportability"]["content_hash"] == "sha256:portfolio-memory"
    transition_event = payload["data"]["events"][2]
    assert transition_event["event_type"] == "BULK_REVIEW_CAMPAIGN_ASSIGNMENT_TASK_TRANSITION"
    assert transition_event["source_refs"] == [
        {"source_system": "lotus-manage", "source_id": "campaign_001:v1"}
    ]
    assert transition_event["artifact_refs"] == [
        {"source_system": "lotus-manage", "source_id": "task_001"}
    ]
    assert transition_event["content_hash"] == "sha256:assignment-task-transition"
    assert transition_event["metadata"]["transition_type"] == "ACKNOWLEDGE"


def test_dpm_command_center_pm_quality_fairness_preview_forwards_segment_refs(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    async def _fake_preview_pm_operating_quality_fairness_analysis(
        self,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "fairness_analysis": {
                "product_name": "PmOperatingQualityFairnessAnalysis",
                "product_version": "v1",
                "fairness_analysis_id": "pmq_fair_001",
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "state": "PENDING_REVIEW",
                "as_of_date": "2026-05-13",
                "minimum_segment_score_run_count": 2,
                "maximum_average_score_spread": "15.00",
                "observed_average_score_spread": "31.00",
                "reason_codes": ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"],
                "blocked_actions": ["CREATE_SCORE_RUN"],
                "forbidden_uses": [
                    "protected_class_inference",
                    "autonomous_pm_ranking",
                    "hr_decision",
                ],
                "segment_results": [
                    {
                        "segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED",
                        "segment_type": "MANDATE_TYPE",
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
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.preview_pm_operating_quality_fairness_analysis",
        _fake_preview_pm_operating_quality_fairness_analysis,
    )

    request_body = {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "as_of_date": "2026-05-13",
        "score_run_ids": ["pmq_run_001", "pmq_run_002"],
        "segments": [
            {
                "segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED",
                "segment_type": "MANDATE_TYPE",
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

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses/preview",
        json={"body": request_body},
        headers={"X-Correlation-Id": "corr-pmq-fairness-router"},
    )

    assert response.status_code == 200
    assert captured == {
        "body": request_body,
        "correlation_id": "corr-pmq-fairness-router",
    }
    payload = response.json()
    assert payload["source_service"] == "lotus-manage"
    assert payload["supportability"]["state"] == "PENDING_REVIEW"
    assert payload["supportability"]["policy_id"] == "pmq_sg_dpm"
    assert payload["supportability"]["fairness_analysis_id"] == "pmq_fair_001"
    assert payload["supportability"]["blocked_actions"] == ["CREATE_SCORE_RUN"]
    analysis = payload["data"]["fairness_analysis"]
    assert analysis["observed_average_score_spread"] == "31.00"
    assert analysis["forbidden_uses"] == [
        "protected_class_inference",
        "autonomous_pm_ranking",
        "hr_decision",
    ]
    assert analysis["segment_results"][0]["source_refs"][0]["source_product"] == ("MandateSegment")


def test_dpm_command_center_pm_quality_fairness_lifecycle_routes_preserve_manage_payloads(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    async def _fake_create_pm_operating_quality_fairness_analysis(
        self,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["create_body"] = body
        captured["create_correlation_id"] = correlation_id
        return 201, {
            "fairness_analysis": {
                "fairness_analysis_id": "pmq_fair_001",
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "state": "PENDING_REVIEW",
                "reason_codes": ["PM_QUALITY_FAIRNESS_SPREAD_REVIEW_REQUIRED"],
                "blocked_actions": ["CREATE_SCORE_RUN"],
                "segment_results": [{"segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED"}],
            }
        }

    async def _fake_list_pm_operating_quality_fairness_analyses(
        self,
        params,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["list_params"] = params
        captured["list_correlation_id"] = correlation_id
        return 200, {
            "count": 1,
            "fairness_analyses": [
                {
                    "fairness_analysis_id": "pmq_fair_001",
                    "policy_id": "pmq_sg_dpm",
                    "policy_version": "2026.05",
                    "state": "PENDING_REVIEW",
                }
            ],
        }

    async def _fake_get_pm_operating_quality_fairness_analysis(
        self,
        fairness_analysis_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["get_fairness_analysis_id"] = fairness_analysis_id
        captured["get_correlation_id"] = correlation_id
        return 200, {
            "fairness_analysis": {
                "fairness_analysis_id": fairness_analysis_id,
                "policy_id": "pmq_sg_dpm",
                "policy_version": "2026.05",
                "state": "PENDING_REVIEW",
                "forbidden_uses": [
                    "protected_class_inference",
                    "autonomous_pm_ranking",
                    "hr_decision",
                ],
            }
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.create_pm_operating_quality_fairness_analysis",
        _fake_create_pm_operating_quality_fairness_analysis,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_pm_operating_quality_fairness_analyses",
        _fake_list_pm_operating_quality_fairness_analyses,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_pm_operating_quality_fairness_analysis",
        _fake_get_pm_operating_quality_fairness_analysis,
    )

    request_body = {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "score_run_ids": ["pmq_run_001", "pmq_run_002"],
        "segments": [{"segment_ref": "MANDATE_TYPE:DISCRETIONARY_BALANCED"}],
    }
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses",
        json={"body": request_body},
        headers={"X-Correlation-Id": "corr-pmq-fairness-create"},
    )
    list_response = client.get(
        (
            "/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses"
            "?policy_id=pmq_sg_dpm&policy_version=2026.05&limit=25&offset=0"
        ),
        headers={"X-Correlation-Id": "corr-pmq-fairness-list"},
    )
    get_response = client.get(
        "/api/v1/dpm/command-center/pm-operating-quality/fairness-analyses/pmq_fair_001",
        headers={"X-Correlation-Id": "corr-pmq-fairness-get"},
    )

    assert create_response.status_code == 200
    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert captured["create_body"] == request_body
    assert captured["create_correlation_id"] == "corr-pmq-fairness-create"
    assert captured["list_params"] == {
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "as_of_date": None,
        "state": None,
        "limit": 25,
        "offset": 0,
    }
    assert captured["list_correlation_id"] == "corr-pmq-fairness-list"
    assert captured["get_fairness_analysis_id"] == "pmq_fair_001"
    assert captured["get_correlation_id"] == "corr-pmq-fairness-get"
    assert create_response.json()["supportability"]["fairness_analysis_id"] == "pmq_fair_001"
    assert list_response.json()["supportability"]["count"] == 1
    assert get_response.json()["data"]["fairness_analysis"]["forbidden_uses"] == [
        "protected_class_inference",
        "autonomous_pm_ranking",
        "hr_decision",
    ]


def test_dpm_command_center_pm_quality_review_action_routes_preserve_manage_payloads(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    review_action = {
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
        "reason_codes": ["PM_QUALITY_REVIEW_ACTION_STATE_REVIEW_REQUIRED"],
        "source_refs": [
            {
                "source_system": "lotus-manage",
                "source_type": "PmOperatingQualityScoreRun",
                "source_id": "pmq_run_001",
            }
        ],
        "forbidden_uses": ["hr_decision", "client_contact", "oms_execution"],
        "operating_boundaries": ["NO_PM_RANKING", "NO_ORDER_OR_OMS_EXECUTION"],
    }

    async def _fake_preview_pm_operating_quality_review_action(
        self,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["preview_body"] = body
        captured["preview_correlation_id"] = correlation_id
        return 200, {"review_action": review_action}

    async def _fake_create_pm_operating_quality_review_action(
        self,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["create_body"] = body
        captured["create_correlation_id"] = correlation_id
        return 201, {"review_action": review_action}

    async def _fake_list_pm_operating_quality_review_actions(
        self,
        params,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["list_params"] = params
        captured["list_correlation_id"] = correlation_id
        return 200, {"count": 1, "review_actions": [review_action], "limit": 25, "offset": 0}

    async def _fake_get_pm_operating_quality_review_action(
        self,
        review_action_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["get_review_action_id"] = review_action_id
        captured["get_correlation_id"] = correlation_id
        return 200, {"review_action": review_action}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.preview_pm_operating_quality_review_action",
        _fake_preview_pm_operating_quality_review_action,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.create_pm_operating_quality_review_action",
        _fake_create_pm_operating_quality_review_action,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_pm_operating_quality_review_actions",
        _fake_list_pm_operating_quality_review_actions,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_pm_operating_quality_review_action",
        _fake_get_pm_operating_quality_review_action,
    )

    request_body = {
        "target_type": "SCORE_RUN",
        "target_id": "pmq_run_001",
        "action_type": "REQUEST_EVIDENCE_REMEDIATION",
        "review_action_ref": "PMQ-REVIEW-2026-05-001",
        "review_reason": "Evidence remediation required before supervisory closure.",
        "actor_id": "ops",
        "source_refs": [],
    }
    client = TestClient(app)

    preview_response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/review-actions/preview",
        json={"body": request_body},
        headers={"X-Correlation-Id": "corr-pmq-review-preview"},
    )
    create_response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/review-actions",
        json={"body": request_body},
        headers={"X-Correlation-Id": "corr-pmq-review-create"},
    )
    list_response = client.get(
        (
            "/api/v1/dpm/command-center/pm-operating-quality/review-actions"
            "?target_type=SCORE_RUN&target_id=pmq_run_001&policy_id=pmq_sg_dpm"
            "&action_state=REVIEW_REQUIRED&limit=25&offset=0"
        ),
        headers={"X-Correlation-Id": "corr-pmq-review-list"},
    )
    get_response = client.get(
        "/api/v1/dpm/command-center/pm-operating-quality/review-actions/pmq_review_001",
        headers={"X-Correlation-Id": "corr-pmq-review-get"},
    )

    assert preview_response.status_code == 200
    assert create_response.status_code == 200
    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert captured["preview_body"] == request_body
    assert captured["create_body"] == request_body
    assert captured["preview_correlation_id"] == "corr-pmq-review-preview"
    assert captured["create_correlation_id"] == "corr-pmq-review-create"
    assert captured["list_params"] == {
        "target_type": "SCORE_RUN",
        "target_id": "pmq_run_001",
        "policy_id": "pmq_sg_dpm",
        "as_of_date": None,
        "action_state": "REVIEW_REQUIRED",
        "limit": 25,
        "offset": 0,
    }
    assert captured["get_review_action_id"] == "pmq_review_001"
    assert captured["get_correlation_id"] == "corr-pmq-review-get"
    assert list_response.json()["supportability"]["review_action_id"] == "pmq_review_001"
    assert get_response.json()["data"]["review_action"]["review_reason"] == (
        "Evidence remediation required before supervisory closure."
    )
    assert get_response.json()["data"]["review_action"]["forbidden_uses"] == [
        "hr_decision",
        "client_contact",
        "oms_execution",
    ]


def test_dpm_command_center_pm_quality_summary_invocation_routes_preserve_manage_payloads(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    summary_invocation = {
        "summary_invocation_id": "pmq_summary_001",
        "score_run_id": "pmq_run_001",
        "review_action_id": "pmq_review_001",
        "policy_id": "pmq_sg_dpm",
        "policy_version": "2026.05",
        "as_of_date": "2026-05-20",
        "invocation_state": "REQUESTED",
        "summary_ref": "PMQ-SUMMARY-2026-05-001",
        "workflow_pack_name": "pm_quality_summary.pack",
        "workflow_pack_version": "v1",
        "workflow_run_id": "packrun_pmq_001",
        "summary_artifact_ref": "artifact://pmq-summary-001",
        "summary_content_hash": "sha256:pmq-summary-artifact-001",
        "requested_by": "ops",
        "reason_codes": ["PM_QUALITY_SUMMARY_INVOCATION_REQUESTED"],
        "source_refs": [
            {
                "source_system": "lotus-ai",
                "source_type": "WorkflowPackRun",
                "source_id": "packrun_pmq_001",
            }
        ],
        "operating_boundaries": [
            "NO_GENERATED_SUMMARY_TEXT_RETENTION",
            "NO_PROMPT_OR_MODEL_RESPONSE_EXPOSURE",
            "NO_PM_RANKING",
            "NO_CLIENT_CONTACT",
            "NO_TRADE_ORDER_OR_OMS_EXECUTION",
        ],
        "text_boundary": {
            "boundary_id": "PM_QUALITY_SUMMARY_TEXT_BOUNDARY",
            "generated_summary_text_stored": False,
            "prompt_body_stored": False,
            "model_response_stored": False,
            "client_communication_projected": False,
            "order_or_oms_projected": False,
            "content_hash": "sha256:pmq-summary-text-boundary",
        },
        "content_hash": "sha256:pmq-summary-invocation-001",
    }

    async def _fake_preview_pm_operating_quality_summary_invocation(
        self,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["preview_body"] = body
        captured["preview_correlation_id"] = correlation_id
        return 200, {"summary_invocation": summary_invocation}

    async def _fake_create_pm_operating_quality_summary_invocation(
        self,
        body,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["create_body"] = body
        captured["create_correlation_id"] = correlation_id
        return 201, {"summary_invocation": summary_invocation}

    async def _fake_list_pm_operating_quality_summary_invocations(
        self,
        params,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["list_params"] = params
        captured["list_correlation_id"] = correlation_id
        return (
            200,
            {"count": 1, "summary_invocations": [summary_invocation], "limit": 25, "offset": 0},
        )

    async def _fake_get_pm_operating_quality_summary_invocation(
        self,
        summary_invocation_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["get_summary_invocation_id"] = summary_invocation_id
        captured["get_correlation_id"] = correlation_id
        return 200, {"summary_invocation": summary_invocation}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.preview_pm_operating_quality_summary_invocation",
        _fake_preview_pm_operating_quality_summary_invocation,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.create_pm_operating_quality_summary_invocation",
        _fake_create_pm_operating_quality_summary_invocation,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_pm_operating_quality_summary_invocations",
        _fake_list_pm_operating_quality_summary_invocations,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_pm_operating_quality_summary_invocation",
        _fake_get_pm_operating_quality_summary_invocation,
    )

    request_body = {
        "score_run_id": "pmq_run_001",
        "review_action_id": "pmq_review_001",
        "summary_ref": "PMQ-SUMMARY-2026-05-001",
        "workflow_run_id": "packrun_pmq_001",
        "summary_artifact_ref": "artifact://pmq-summary-001",
        "summary_content_hash": "sha256:pmq-summary-artifact-001",
        "requested_by": "ops",
        "source_refs": [],
    }
    client = TestClient(app)

    preview_response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations/preview",
        json={"body": request_body},
        headers={"X-Correlation-Id": "corr-pmq-summary-preview"},
    )
    create_response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations",
        json={"body": request_body},
        headers={"X-Correlation-Id": "corr-pmq-summary-create"},
    )
    list_response = client.get(
        (
            "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations"
            "?score_run_id=pmq_run_001&review_action_id=pmq_review_001&policy_id=pmq_sg_dpm"
            "&invocation_state=REQUESTED&limit=25&offset=0"
        ),
        headers={"X-Correlation-Id": "corr-pmq-summary-list"},
    )
    get_response = client.get(
        "/api/v1/dpm/command-center/pm-operating-quality/summary-invocations/pmq_summary_001",
        headers={"X-Correlation-Id": "corr-pmq-summary-get"},
    )

    assert preview_response.status_code == 200
    assert create_response.status_code == 200
    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert captured["preview_body"] == request_body
    assert captured["create_body"] == request_body
    assert captured["list_params"] == {
        "score_run_id": "pmq_run_001",
        "review_action_id": "pmq_review_001",
        "policy_id": "pmq_sg_dpm",
        "as_of_date": None,
        "invocation_state": "REQUESTED",
        "limit": 25,
        "offset": 0,
    }
    assert captured["get_summary_invocation_id"] == "pmq_summary_001"
    assert list_response.json()["supportability"]["summary_invocation_id"] == "pmq_summary_001"
    assert (
        get_response.json()["data"]["summary_invocation"]["text_boundary"][
            "generated_summary_text_stored"
        ]
        is False
    )
    assert (
        get_response.json()["data"]["summary_invocation"]["text_boundary"]["model_response_stored"]
        is False
    )


def test_dpm_command_center_outcome_review_create_preserves_manage_truth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_create_outcome_review(self, body, correlation_id):  # noqa: ANN001
        _ = self
        captured["body"] = body
        captured["correlation_id"] = correlation_id
        return 200, {
            "outcome_review_id": "or_1",
            "state": "READY",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "expected_snapshot_hash": "sha256:expected",
            "realized_snapshot_hash": "sha256:realized",
            "supportability": {
                "state": "SUPPORTED",
                "reason_codes": ["READY_FOR_REPORT_INPUT"],
                "blocked_actions": [],
            },
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.create_outcome_review",
        _fake_create_outcome_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/outcome-reviews",
        json={"body": {"rebalance_run_id": "rr_1", "proof_pack_id": "ppack_1"}},
        headers={"X-Correlation-Id": "corr-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured == {
        "body": {"rebalance_run_id": "rr_1", "proof_pack_id": "ppack_1"},
        "correlation_id": "corr-router-1",
    }
    assert payload["correlation_id"] == "corr-router-1"
    assert payload["source_service"] == "lotus-manage"
    assert payload["supportability"]["state"] == "SUPPORTED"
    assert payload["data"]["expected_snapshot_hash"] == "sha256:expected"
    assert payload["data"]["realized_snapshot_hash"] == "sha256:realized"


def test_dpm_command_center_outcome_review_list_passes_filters(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_list_outcome_reviews(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["params"] = params
        captured["correlation_id"] = correlation_id
        return 200, {
            "items": [{"outcome_review_id": "or_1", "state": "READY"}],
            "next_cursor": None,
            "supportability": {"state": "SUPPORTED"},
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_outcome_reviews",
        _fake_list_outcome_reviews,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/dpm/command-center/outcome-reviews"
        "?portfolio_id=PB_SG_GLOBAL_BAL_001&state=READY&limit=10",
        headers={"X-Correlation-Id": "corr-router-2"},
    )

    assert response.status_code == 200
    assert captured == {
        "params": {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "rebalance_run_id": None,
            "wave_id": None,
            "state": "READY",
            "limit": 10,
            "cursor": None,
        },
        "correlation_id": "corr-router-2",
    }
    assert response.json()["data"]["items"][0]["outcome_review_id"] == "or_1"


def test_dpm_command_center_outcome_review_boundary_is_preserved_in_handoffs(
    monkeypatch,
) -> None:
    boundary = _client_communication_boundary()
    captured: dict[str, object] = {}

    async def _fake_get_outcome_review_supportability(
        self,
        outcome_review_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["supportability"] = {
            "outcome_review_id": outcome_review_id,
            "correlation_id": correlation_id,
        }
        return 200, {
            "outcome_review_id": outcome_review_id,
            "state": "SUPPORTED",
            "client_communication_boundary": boundary,
            "supportability": {
                "state": "SUPPORTED",
                "reason_codes": ["READY_FOR_REPORT_INPUT"],
                "blocked_actions": [],
            },
        }

    async def _fake_get_outcome_review_report_input(
        self,
        outcome_review_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["report_input"] = {
            "outcome_review_id": outcome_review_id,
            "correlation_id": correlation_id,
        }
        return 200, {
            "outcome_review_id": outcome_review_id,
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "content_hash": "sha256:report-input",
            "client_communication_boundary": boundary,
        }

    async def _fake_get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["ai_evidence_input"] = {
            "outcome_review_id": outcome_review_id,
            "correlation_id": correlation_id,
        }
        payload = _outcome_ai_evidence(outcome_review_id)
        payload["client_communication_boundary"] = boundary
        return 200, payload

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review_supportability",
        _fake_get_outcome_review_supportability,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review_report_input",
        _fake_get_outcome_review_report_input,
    )
    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review_ai_evidence_input",
        _fake_get_outcome_review_ai_evidence_input,
    )

    client = TestClient(app)
    supportability_response = client.get(
        "/api/v1/dpm/command-center/outcome-reviews/or_1/supportability",
        headers={"X-Correlation-Id": "corr-boundary-supportability"},
    )
    report_response = client.get(
        "/api/v1/dpm/command-center/outcome-reviews/or_1/report-input",
        headers={"X-Correlation-Id": "corr-boundary-report"},
    )
    ai_response = client.get(
        "/api/v1/dpm/command-center/outcome-reviews/or_1/ai-evidence-input",
        headers={"X-Correlation-Id": "corr-boundary-ai"},
    )

    assert supportability_response.status_code == 200
    assert report_response.status_code == 200
    assert ai_response.status_code == 200
    assert captured == {
        "supportability": {
            "outcome_review_id": "or_1",
            "correlation_id": "corr-boundary-supportability",
        },
        "report_input": {
            "outcome_review_id": "or_1",
            "correlation_id": "corr-boundary-report",
        },
        "ai_evidence_input": {
            "outcome_review_id": "or_1",
            "correlation_id": "corr-boundary-ai",
        },
    }

    for payload in (
        supportability_response.json()["data"],
        report_response.json()["data"],
        ai_response.json()["data"],
    ):
        assert payload["client_communication_boundary"] == boundary
        assert (
            payload["client_communication_boundary"]["boundary_id"]
            == "DPM_OUTCOME_CLIENT_COMMUNICATION_BOUNDARY"
        )
        assert payload["client_communication_boundary"]["client_communication_projected"] is False
        assert payload["client_communication_boundary"]["client_approval_projected"] is False
        assert (
            payload["client_communication_boundary"]["required_source_product"]
            == "ClientCommunicationRecord:v1"
        )


def test_dpm_command_center_outcome_review_error_is_not_marked_supported(monkeypatch) -> None:
    async def _fake_get_outcome_review(self, outcome_review_id, correlation_id):  # noqa: ANN001
        _ = self, outcome_review_id, correlation_id
        return 404, {"detail": "outcome review not found"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review",
        _fake_get_outcome_review,
    )

    client = TestClient(app)
    response = client.get("/api/v1/dpm/command-center/outcome-reviews/or_missing")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR"
    assert response.json()["detail"]["detail"] == "outcome review not found"


def test_dpm_command_center_outcome_review_ai_narrative_executes_lotus_ai(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_outcome_review_ai_evidence_input(
        self,
        outcome_review_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["manage"] = {
            "outcome_review_id": outcome_review_id,
            "correlation_id": correlation_id,
        }
        return 200, _outcome_ai_evidence(outcome_review_id)

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        _ = self
        captured["ai"] = kwargs
        return 200, {
            "execution": {
                "status": "COMPLETED",
                "audit": {"workflow_pack_run_id": "packrun_or_1"},
                "result": {
                    "structured_output": {
                        "outcome_review_narrative_status": "REVIEW_REQUIRED",
                        "evidence_content_hash": "sha256:or_1-ai-evidence",
                    }
                },
            },
            "workflow_pack_run": {
                "run_id": "packrun_or_1",
                "workflow_authority_owner": "lotus-manage",
            },
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_outcome_review_ai_evidence_input",
        _fake_get_outcome_review_ai_evidence_input,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/outcome-reviews/or_1/ai-narrative",
        json={"requested_outputs": ["pm_summary", "evidence_gaps"], "audience": ["pm"]},
        headers={"X-Correlation-Id": "corr-ai-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["manage"] == {
        "outcome_review_id": "or_1",
        "correlation_id": "corr-ai-router-1",
    }
    ai_call = captured["ai"]
    assert ai_call["pack_id"] == "outcome_review_narrative.pack"
    assert ai_call["correlation_id"] == "corr-ai-router-1"
    assert ai_call["task_request"]["caller"]["caller_app"] == "lotus-gateway"
    assert payload["source_service"] == "lotus-ai"
    assert payload["evidence_source_service"] == "lotus-manage"
    assert payload["ai_evidence_input"]["content_hash"] == "sha256:or_1-ai-evidence"
    assert payload["ai_evidence_input"]["client_communication_boundary"] == (
        _client_communication_boundary()
    )
    assert payload["data"]["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def test_dpm_command_center_exception_summary_executes_lotus_ai(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_list_monitoring_exceptions(self, params, correlation_id):  # noqa: ANN001
        _ = self
        captured["manage"] = {
            "params": params,
            "correlation_id": correlation_id,
        }
        return 200, _exception_page()

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        _ = self
        captured["ai"] = kwargs
        return 200, {
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
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_monitoring_exceptions",
        _fake_list_monitoring_exceptions,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/exceptions/me_source_1/ai-summary",
        json={
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "state": "ACTIVE",
            "requested_outputs": ["exception_summary", "recommended_triage"],
            "audience": ["portfolio_manager", "operations"],
        },
        headers={"X-Correlation-Id": "corr-exception-router-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["manage"] == {
        "params": {
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "mandate_id": None,
            "state": "ACTIVE",
            "limit": 200,
        },
        "correlation_id": "corr-exception-router-1",
    }
    ai_call = captured["ai"]
    assert ai_call["pack_id"] == "dpm_exception_summary.pack"
    assert ai_call["workflow_surface"] == "dpm-exception-summary-ai-evidence"
    assert ai_call["correlation_id"] == "corr-exception-router-1"
    task_request = ai_call["task_request"]
    assert task_request["caller"]["caller_app"] == "lotus-gateway"
    context_payload = task_request["context"]["payload"]
    assert context_payload["exception_summary_request"] == {
        "requested_outputs": ["exception_summary", "recommended_triage"],
        "audience": ["portfolio_manager", "operations"],
    }
    assert context_payload["supportability"]["requires_human_review"] is True
    assert "place_orders" in context_payload["supportability"]["forbidden_actions"]
    assert "portfolio_manager_scoring" in context_payload["supportability"]["unsupported_claims"]
    assert payload["source_service"] == "lotus-ai"
    assert payload["evidence_source_service"] == "lotus-manage"
    assert payload["exception_summary_input"]["redaction_policy"] == "NO_RAW_PAYLOADS"
    assert payload["exception_summary_input"]["exceptions"][0]["exception_id"] == "me_source_1"
    assert payload["data"]["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def test_dpm_command_center_pm_quality_summary_executes_lotus_ai(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_get_pm_operating_quality_score_run(
        self,
        score_run_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self
        captured["manage"] = {
            "score_run_id": score_run_id,
            "correlation_id": correlation_id,
        }
        return 200, {"score_run": _pm_quality_score_run(score_run_id)}

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        _ = self
        captured["ai"] = kwargs
        return 200, {
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
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_pm_operating_quality_score_run",
        _fake_get_pm_operating_quality_score_run,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/score-runs/pmq_run_001/ai-summary",
        json={
            "requested_outputs": ["score_run_summary", "fairness_review_posture"],
            "audience": ["portfolio_manager", "investment_control"],
        },
        headers={"X-Correlation-Id": "corr-pmq-summary-router"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["manage"] == {
        "score_run_id": "pmq_run_001",
        "correlation_id": "corr-pmq-summary-router",
    }
    ai_call = captured["ai"]
    assert ai_call["pack_id"] == "pm_quality_summary.pack"
    assert ai_call["version"] == "v1"
    assert ai_call["workflow_surface"] == "dpm-pm-quality-ai-evidence"
    assert ai_call["correlation_id"] == "corr-pmq-summary-router"
    task_request = ai_call["task_request"]
    assert task_request["caller"]["caller_app"] == "lotus-gateway"
    context_payload = task_request["context"]["payload"]
    assert context_payload["score_run"]["score_run_id"] == "pmq_run_001"
    assert context_payload["summary_request"] == {
        "requested_outputs": ["score_run_summary", "fairness_review_posture"],
        "audience": ["portfolio_manager", "investment_control"],
    }
    assert "rank_portfolio_managers" in context_payload["supportability"]["forbidden_actions"]
    assert "execution_instruction" in context_payload["supportability"]["unsupported_claims"]
    assert payload["source_service"] == "lotus-ai"
    assert payload["evidence_source_service"] == "lotus-manage"
    assert payload["score_run"]["score_run_id"] == "pmq_run_001"
    assert payload["data"]["workflow_pack_run"]["workflow_authority_owner"] == "lotus-manage"


def test_dpm_command_center_pm_quality_summary_rejects_unsupported_outputs(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {"manage_called": False, "ai_called": False}

    async def _fake_get_pm_operating_quality_score_run(
        self,
        score_run_id,
        correlation_id,
    ):  # noqa: ANN001
        _ = self, score_run_id, correlation_id
        captured["manage_called"] = True
        return 200, {"score_run": _pm_quality_score_run("pmq_run_001")}

    async def _fake_execute_workflow_pack(self, **kwargs):  # noqa: ANN003
        _ = self, kwargs
        captured["ai_called"] = True
        return 200, {}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_pm_operating_quality_score_run",
        _fake_get_pm_operating_quality_score_run,
    )
    monkeypatch.setattr(
        "app.clients.lotus_ai_client.LotusAiClient.execute_workflow_pack",
        _fake_execute_workflow_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/dpm/command-center/pm-operating-quality/score-runs/pmq_run_001/ai-summary",
        json={
            "requested_outputs": ["score_run_summary", "pm_ranking"],
            "audience": ["portfolio_manager"],
        },
        headers={"X-Correlation-Id": "corr-pmq-summary-router"},
    )

    assert response.status_code == 422
    assert "Unsupported PM quality summary outputs requested" in response.text
    assert captured == {"manage_called": False, "ai_called": False}


def _outcome_ai_evidence(outcome_review_id: str) -> dict[str, object]:
    return {
        "contract_version": "1.0",
        "outcome_review_id": outcome_review_id,
        "outcome_review_content_hash": "sha256:outcome-review",
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
        "source_refs": [],
        "evidence_ref": {
            "source_id": f"{outcome_review_id}:dpm_outcome_ai_evidence_input",
            "content_hash": f"sha256:{outcome_review_id}-ai-evidence",
        },
        "client_communication_boundary": _client_communication_boundary(),
        "content_hash": f"sha256:{outcome_review_id}-ai-evidence",
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


def _pm_quality_score_run(score_run_id: str) -> dict[str, object]:
    return {
        "product_name": "PmOperatingQualityScoreRun",
        "product_version": "1.0",
        "score_run_id": score_run_id,
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
                        "source_id": score_run_id,
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
                "source_id": score_run_id,
                "content_hash": "sha256:pmq-run-001",
            }
        ],
        "content_hash": "sha256:pmq-run-001",
    }
