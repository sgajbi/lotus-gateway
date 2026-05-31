from app.services.dpm_command_center_supportability import (
    command_center_supportability_from,
    outcome_review_supportability_from,
    pm_operating_quality_supportability_from,
    portfolio_memory_supportability_from,
)


def test_command_center_supportability_derives_mandate_partial_readiness() -> None:
    supportability = command_center_supportability_from(
        {
            "mandate_id": "mandate-1",
            "portfolio_id": "portfolio-1",
            "mandate_version": 7,
            "field_gap_codes": ["MISSING_RESTRICTIONS"],
        }
    )

    assert supportability.model_dump() == {
        "state": "PARTIAL",
        "data_completeness_state": "PARTIAL",
        "partial_readiness_reasons": [
            "MISSING_RESTRICTIONS",
            "SOURCE_LINEAGE_NOT_PUBLISHED",
        ],
        "source_run_id": "7",
        "remediation_owner": "Portfolio Operations",
        "source_service": "lotus-manage",
        "authority": "lotus-manage:RFC-0038",
    }


def test_command_center_supportability_prefers_manage_supportability_block() -> None:
    supportability = command_center_supportability_from(
        {
            "mandate_id": "mandate-1",
            "portfolio_id": "portfolio-1",
            "field_gap_codes": ["MISSING_RESTRICTIONS"],
            "supportability": {
                "supportabilityState": "READY",
                "dataCompletenessState": "READY",
                "partialReadinessReasons": [],
                "sourceRunId": "run-42",
                "remediationOwner": "DPM Operations",
            },
        }
    )

    assert supportability.model_dump() == {
        "state": "READY",
        "data_completeness_state": "READY",
        "partial_readiness_reasons": [],
        "source_run_id": "run-42",
        "remediation_owner": "DPM Operations",
        "source_service": "lotus-manage",
        "authority": "lotus-manage:RFC-0038",
    }


def test_outcome_review_supportability_preserves_counts_and_boundaries() -> None:
    supportability = outcome_review_supportability_from(
        {
            "supportability": {
                "supportabilityState": "BLOCKED",
                "reasonCodes": ["MISSING_EXECUTION_OUTCOME", 42],
                "blockedActions": ["release_report"],
                "remediationOwner": "Portfolio Operations",
            },
            "applied_filters": {"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
            "source_owner_counts": {"lotus-manage": "3", "bad": "not-int", "bool": True},
            "source_type_counts": {"outcome_review": 2},
            "support_boundary": {"authority": "lotus-manage"},
        }
    )

    assert supportability.model_dump() == {
        "state": "BLOCKED",
        "reason_codes": ["MISSING_EXECUTION_OUTCOME", "42"],
        "blocked_actions": ["release_report"],
        "remediation_owner": "Portfolio Operations",
        "applied_filters": {"portfolio_id": "PB_SG_GLOBAL_BAL_001"},
        "source_owner_counts": {"lotus-manage": 3, "bad": 0, "bool": 0},
        "source_type_counts": {"outcome_review": 2},
        "support_boundary": {"authority": "lotus-manage"},
        "source_service": "lotus-manage",
        "authority": "lotus-manage:RFC-0042",
    }


def test_pm_operating_quality_supportability_uses_first_score_run_and_policy() -> None:
    supportability = pm_operating_quality_supportability_from(
        {
            "count": "2",
            "policy_id": "pm-quality",
            "policy_version": "v3",
            "score_runs": [
                {
                    "score_run_id": "score-1",
                    "supportabilityState": "READY",
                    "fairness_analysis_id": "fairness-1",
                    "reason_codes": ["SOURCE_READY"],
                    "blockedActions": ["contact_client"],
                }
            ],
        }
    )

    assert supportability.model_dump() == {
        "state": "READY",
        "reason_codes": ["SOURCE_READY"],
        "blocked_actions": ["contact_client"],
        "policy_id": "pm-quality",
        "policy_version": "v3",
        "score_run_id": "score-1",
        "fairness_analysis_id": "fairness-1",
        "review_action_id": None,
        "summary_invocation_id": None,
        "count": 2,
        "source_service": "lotus-manage",
        "authority": "lotus-manage:RFC-0042/PM_OPERATING_QUALITY",
    }


def test_portfolio_memory_supportability_coerces_counts_and_content_hash() -> None:
    supportability = portfolio_memory_supportability_from(
        {
            "supportabilityState": "DEGRADED",
            "eventCount": "5",
            "event_type_counts": {"decision": "4", "negative": -2},
            "source_systems": ["lotus-manage", 100],
            "source_system_counts": {"lotus-manage": 5},
            "source_type_counts": {"portfolio_memory_event": "5"},
            "reason_codes": ["PARTIAL_HISTORY"],
            "content_hash": 12345,
        }
    )

    assert supportability.model_dump() == {
        "state": "DEGRADED",
        "event_count": 5,
        "event_type_counts": {"decision": 4, "negative": 0},
        "source_systems": ["lotus-manage", "100"],
        "source_system_counts": {"lotus-manage": 5},
        "source_type_counts": {"portfolio_memory_event": 5},
        "reason_codes": ["PARTIAL_HISTORY"],
        "content_hash": "12345",
        "source_service": "lotus-manage",
        "authority": "lotus-manage:RFC-0040/RFC-0041/RFC-0042",
    }
