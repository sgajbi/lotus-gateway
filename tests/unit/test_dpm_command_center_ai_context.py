from app.contracts.dpm_command_center import (
    DpmCommandCenterSupportability,
    DpmOutcomeReviewSupportability,
    DpmPmOperatingQualitySupportability,
)
from app.services.dpm_command_center_ai_context import (
    exception_summary_input_from_exception,
    exception_summary_source_refs,
    exception_summary_task_payload,
    find_exception,
    outcome_ai_source_refs,
    outcome_review_narrative_task_payload,
    pm_quality_score_run_from,
    pm_quality_summary_source_refs,
    pm_quality_summary_task_payload,
)


def test_pm_quality_score_run_source_refs_preserve_lineage_and_policy_refs() -> None:
    score_run = {
        "score_run_id": "pmq-run-001",
        "policy_id": "pm-quality",
        "policy_version": 3,
        "source_refs": [
            "lotus-manage:existing-ref:1",
            {
                "sourceSystem": "lotus-core",
                "product_name": "PortfolioStateSnapshot",
                "sourceId": "PB_SG_GLOBAL_BAL_001",
            },
            {"missing": "ignored"},
            "lotus-manage:existing-ref:1",
        ],
    }

    assert pm_quality_summary_source_refs(score_run) == [
        "lotus-core:PortfolioStateSnapshot:PB_SG_GLOBAL_BAL_001",
        "lotus-manage:existing-ref:1",
        "lotus-manage:pm-quality-policy:pm-quality:3",
        "lotus-manage:pm-quality-score-run:pmq-run-001",
    ]


def test_pm_quality_score_run_from_accepts_embedded_or_flat_payload() -> None:
    embedded = {"score_run": {"score_run_id": "embedded"}}
    flat = {"score_run_id": "flat"}
    unrelated = {"count": 0}

    assert pm_quality_score_run_from(embedded) == {"score_run_id": "embedded"}
    assert pm_quality_score_run_from(flat) == flat
    assert pm_quality_score_run_from(unrelated) is None


def test_find_exception_matches_only_manage_exception_items() -> None:
    payload = {
        "items": [
            {"exception_id": "other"},
            "ignored",
            {"exception_id": "target", "state": "OPEN"},
        ]
    }

    assert find_exception(payload, "target") == {"exception_id": "target", "state": "OPEN"}
    assert find_exception(payload, "missing") is None
    assert find_exception({"items": "not-a-list"}, "target") is None


def test_exception_summary_input_bounds_raw_exception_and_preserves_lineage_refs() -> None:
    exception_summary_input = exception_summary_input_from_exception(
        {
            "exception_id": "me-1",
            "portfolio_id": "PB_SG_GLOBAL_BAL_001",
            "mandate_id": 1001,
            "severity": "HIGH",
            "state": "OPEN",
            "reason_code": "MANDATE_BREACH",
            "recommended_action": "REVIEW_WITH_PM",
            "detected_at": "2026-05-31T08:00:00Z",
            "as_of_date": "2026-05-31",
            "source_lineage": [
                {
                    "source_system": "lotus-core",
                    "source_type": "PortfolioStateSnapshot",
                    "source_id": "snapshot-1",
                    "content_hash": "sha256:snapshot",
                },
                {
                    "sourceSystem": "lotus-manage",
                    "product_name": "PortfolioActionRegister",
                    "product_version": "v1",
                },
                {"source_system": "ignored"},
            ],
            "raw_payload": {"must_not": "leak"},
        }
    )

    content_hash = exception_summary_input["content_hash"]
    assert isinstance(content_hash, str)
    assert content_hash.startswith("sha256:")
    assert exception_summary_input["portfolio_id"] == "PB_SG_GLOBAL_BAL_001"
    assert exception_summary_input["mandate_id"] == "1001"
    assert exception_summary_input["as_of_date"] == "2026-05-31"
    assert exception_summary_input["exception_count"] == 1
    assert exception_summary_input["redaction_policy"] == "NO_RAW_PAYLOADS"
    assert "raw_payload" not in str(exception_summary_input)
    assert exception_summary_input["evidence_ref"] == {
        "source_system": "lotus-manage",
        "source_type": "DPM_EXCEPTION_SUMMARY_INPUT",
        "source_id": "PB_SG_GLOBAL_BAL_001:dpm_exception_summary_input:me-1",
        "content_hash": content_hash,
    }
    bounded_exception = exception_summary_input["exceptions"][0]
    assert bounded_exception["source_refs"] == [
        {
            "source_system": "lotus-manage",
            "source_type": "DPM_MONITORING_EXCEPTION",
            "source_id": "me-1",
            "content_hash": content_hash,
        },
        {
            "source_system": "lotus-core",
            "source_type": "PortfolioStateSnapshot",
            "source_id": "snapshot-1",
            "content_hash": "sha256:snapshot",
        },
        {
            "source_system": "lotus-manage",
            "source_type": "PortfolioActionRegister",
            "source_id": "v1",
            "content_hash": content_hash,
        },
    ]


def test_exception_summary_source_refs_and_outcome_ai_refs_are_stable() -> None:
    exception_summary_input = {
        "content_hash": "sha256:exception-input",
        "exceptions": [{"exception_id": "me-1"}, {"exception_id": "me-1"}],
    }

    assert exception_summary_source_refs(exception_summary_input) == [
        "lotus-manage:exception-summary:sha256:exception-input",
        "lotus-manage:monitoring-exception:me-1",
    ]
    assert outcome_ai_source_refs(
        {"evidence_ref": {"source_id": "evidence-1"}},
        "or-1",
    ) == [
        "lotus-manage:outcome-review:or-1",
        "lotus-manage:outcome-ai-evidence:evidence-1",
    ]
    assert outcome_ai_source_refs({}, "or-1") == [
        "lotus-manage:outcome-review:or-1",
        "lotus-manage:outcome-ai-evidence:or-1",
    ]


def test_ai_handoff_task_payloads_preserve_review_boundaries() -> None:
    exception_payload = exception_summary_task_payload(
        exception_summary_input={"exception_id": "me-1"},
        summary_request={"requested_outputs": ["summary"], "audience": ["pm"]},
        supportability=DpmCommandCenterSupportability(
            state="READY",
            data_completeness_state="READY",
            partial_readiness_reasons=[],
        ),
    )
    assert exception_payload["supportability"] == {
        "source_state": "READY",
        "reason_codes": [],
        "blocked_actions": [],
        "forbidden_actions": [
            "approve_rebalance",
            "contact_client",
            "invent_missing_evidence",
            "override_controls",
            "place_orders",
            "score_portfolio_manager",
        ],
        "requires_human_review": True,
        "unsupported_claims": [
            "trade_approval",
            "order_instruction",
            "client_message",
            "portfolio_manager_scoring",
        ],
    }

    narrative_payload = outcome_review_narrative_task_payload(
        ai_evidence_input={"outcome_review_id": "or-1"},
        narrative_request={"requested_outputs": ["pm_summary"], "audience": ["pm"]},
        supportability=DpmOutcomeReviewSupportability(
            state="BLOCKED",
            reason_codes=["MISSING_EVIDENCE"],
            blocked_actions=["release_report"],
        ),
    )
    assert narrative_payload["supportability"] == {
        "source_state": "BLOCKED",
        "reason_codes": ["MISSING_EVIDENCE"],
        "blocked_actions": ["release_report"],
        "requires_human_review": True,
        "unsupported_claims": [
            "client_contact",
            "trade_approval",
            "portfolio_manager_scoring",
        ],
    }

    pm_quality_payload = pm_quality_summary_task_payload(
        manage_payload={"portfolio_memory_context": {"portfolio_id": "PB_SG_GLOBAL_BAL_001"}},
        score_run={"score_run_id": "score-1"},
        summary_request={"requested_outputs": ["summary"], "audience": ["cio"]},
        supportability=DpmPmOperatingQualitySupportability(state="READY"),
    )
    assert pm_quality_payload["score_run"] == {"score_run_id": "score-1"}
    assert pm_quality_payload["portfolio_memory_context"] == {
        "portfolio_id": "PB_SG_GLOBAL_BAL_001"
    }
    assert pm_quality_payload["supportability"]["requires_human_review"] is True
    assert "contact_client" in pm_quality_payload["supportability"]["forbidden_actions"]
    assert "trade_approval" in pm_quality_payload["supportability"]["unsupported_claims"]
