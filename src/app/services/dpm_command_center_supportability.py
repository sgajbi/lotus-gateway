"""Supportability mappers for DPM command-center Gateway envelopes."""

from typing import Any

from app.contracts.dpm_command_center import (
    DpmCommandCenterSupportability,
    DpmOutcomeReviewSupportability,
    DpmPmOperatingQualitySupportability,
    DpmPortfolioMemorySupportability,
)


def pm_operating_quality_supportability_from(
    payload: dict[str, Any],
) -> DpmPmOperatingQualitySupportability:
    supportability_source, policy = _pm_operating_quality_supportability_source(payload)
    state = (
        supportability_source.get("state")
        or supportability_source.get("action_state")
        or supportability_source.get("supportability_state")
        or supportability_source.get("supportabilityState")
        or ("EMPTY" if safe_int(payload.get("count")) == 0 else None)
        or "UNKNOWN"
    )
    return DpmPmOperatingQualitySupportability(
        state=str(state),
        reason_codes=list_of_strings(supportability_source.get("reason_codes") or []),
        blocked_actions=list_of_strings(
            supportability_source.get("blocked_actions")
            or supportability_source.get("blockedActions")
            or []
        ),
        policy_id=safe_optional_str(policy.get("policy_id")),
        policy_version=safe_optional_str(policy.get("policy_version")),
        score_run_id=safe_optional_str(supportability_source.get("score_run_id")),
        fairness_analysis_id=safe_optional_str(supportability_source.get("fairness_analysis_id")),
        review_action_id=safe_optional_str(supportability_source.get("review_action_id")),
        summary_invocation_id=safe_optional_str(supportability_source.get("summary_invocation_id")),
        count=safe_int(payload.get("count")) if "count" in payload else None,
    )


def _pm_operating_quality_supportability_source(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    score_run = payload.get("score_run")
    fairness_analysis = payload.get("fairness_analysis")
    review_action = payload.get("review_action")
    summary_invocation = payload.get("summary_invocation")
    policy = payload
    if isinstance(summary_invocation, dict):
        return summary_invocation, summary_invocation
    if isinstance(review_action, dict):
        return review_action, review_action
    if isinstance(fairness_analysis, dict):
        return fairness_analysis, fairness_analysis
    if isinstance(score_run, dict):
        return score_run, score_run
    if isinstance(payload.get("review_actions"), list):
        supportability_source = first_dict(payload["review_actions"]) or payload
        return supportability_source, supportability_source
    if isinstance(payload.get("summary_invocations"), list):
        supportability_source = first_dict(payload["summary_invocations"]) or payload
        return supportability_source, supportability_source
    if isinstance(payload.get("fairness_analyses"), list):
        supportability_source = first_dict(payload["fairness_analyses"]) or payload
        return supportability_source, supportability_source
    if isinstance(payload.get("score_runs"), list):
        return first_dict(payload["score_runs"]) or payload, policy
    if isinstance(payload.get("policies"), list):
        supportability_source = first_dict(payload["policies"]) or payload
        return supportability_source, supportability_source
    return payload, policy


def outcome_review_supportability_from(payload: dict[str, Any]) -> DpmOutcomeReviewSupportability:
    raw = payload.get("supportability")
    supportability = raw if isinstance(raw, dict) else payload
    reason_codes = list_of_strings(
        supportability.get("reason_codes")
        or supportability.get("reasonCodes")
        or supportability.get("reasons")
        or []
    )
    blocked_actions = list_of_strings(
        supportability.get("blocked_actions") or supportability.get("blockedActions") or []
    )
    state = (
        supportability.get("state")
        or supportability.get("supportability_state")
        or supportability.get("supportabilityState")
        or "UNKNOWN"
    )
    remediation_owner = supportability.get("remediation_owner") or supportability.get(
        "remediationOwner"
    )

    return DpmOutcomeReviewSupportability(
        state=str(state),
        reason_codes=reason_codes,
        blocked_actions=blocked_actions,
        remediation_owner=str(remediation_owner) if remediation_owner is not None else None,
        applied_filters=dict_of_objects(payload.get("applied_filters")),
        source_owner_counts=dict_of_ints(payload.get("source_owner_counts")),
        source_type_counts=dict_of_ints(payload.get("source_type_counts")),
        support_boundary=dict_of_objects(payload.get("support_boundary")),
    )


def command_center_supportability_from(
    payload: dict[str, Any],
) -> DpmCommandCenterSupportability:
    raw = payload.get("supportability")
    supportability = raw if isinstance(raw, dict) else {}
    mandate_supportability = mandate_payload_supportability(payload)
    if mandate_supportability is not None and not supportability:
        return mandate_supportability
    data_completeness_state = supportability.get("data_completeness_state") or supportability.get(
        "dataCompletenessState"
    )
    state = (
        supportability.get("state")
        or supportability.get("supportability_state")
        or supportability.get("supportabilityState")
        or data_completeness_state
        or payload.get("command_center_state")
        or payload.get("state")
        or "UNKNOWN"
    )
    source_run_id = (
        supportability.get("source_run_id")
        or supportability.get("sourceRunId")
        or payload.get("monitoring_run_id")
    )
    remediation_owner = supportability.get("remediation_owner") or supportability.get(
        "remediationOwner"
    )
    partial_reasons = list_of_strings(
        supportability.get("partial_readiness_reasons")
        or supportability.get("partialReadinessReasons")
        or supportability.get("reason_codes")
        or supportability.get("reasonCodes")
        or []
    )

    return DpmCommandCenterSupportability(
        state=str(state),
        data_completeness_state=(
            str(data_completeness_state) if data_completeness_state is not None else None
        ),
        partial_readiness_reasons=partial_reasons,
        source_run_id=str(source_run_id) if source_run_id is not None else None,
        remediation_owner=str(remediation_owner) if remediation_owner is not None else None,
    )


def mandate_payload_supportability(
    payload: dict[str, Any],
) -> DpmCommandCenterSupportability | None:
    if "mandate_id" not in payload or "portfolio_id" not in payload:
        return None
    field_gap_codes = list_of_strings(payload.get("field_gap_codes") or [])
    source_lineage = payload.get("source_lineage")
    has_source_lineage = isinstance(source_lineage, list) and bool(source_lineage)
    state = "PARTIAL" if field_gap_codes else "READY"
    if not has_source_lineage:
        state = "PARTIAL"
        field_gap_codes = [*field_gap_codes, "SOURCE_LINEAGE_NOT_PUBLISHED"]
    return DpmCommandCenterSupportability(
        state=state,
        data_completeness_state=state,
        partial_readiness_reasons=field_gap_codes,
        source_run_id=safe_optional_str(payload.get("mandate_version")),
        remediation_owner="Portfolio Operations" if field_gap_codes else None,
    )


def portfolio_memory_supportability_from(
    payload: dict[str, Any],
) -> DpmPortfolioMemorySupportability:
    state = (
        payload.get("supportability_state")
        or payload.get("supportabilityState")
        or payload.get("state")
        or "UNKNOWN"
    )
    event_count = payload.get("event_count") or payload.get("eventCount") or 0
    return DpmPortfolioMemorySupportability(
        state=str(state),
        event_count=safe_int(event_count),
        event_type_counts=dict_of_ints(payload.get("event_type_counts")),
        source_systems=list_of_strings(payload.get("source_systems") or []),
        source_system_counts=dict_of_ints(payload.get("source_system_counts")),
        source_type_counts=dict_of_ints(payload.get("source_type_counts")),
        reason_codes=list_of_strings(payload.get("reason_codes") or []),
        content_hash=safe_optional_str(payload.get("content_hash")),
    )


def first_dict(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list) or not value:
        return None
    first = value[0]
    return first if isinstance(first, dict) else None


def list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def dict_of_ints(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    counts: dict[str, int] = {}
    for key, count in value.items():
        counts[str(key)] = safe_int(count)
    return counts


def dict_of_objects(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def safe_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, str):
        try:
            return max(int(value), 0)
        except ValueError:
            return 0
    return 0


def safe_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
