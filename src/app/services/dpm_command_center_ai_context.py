"""AI handoff context builders for DPM command-center Gateway workflows."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from app.contracts.dpm_command_center import (
    DpmCommandCenterSupportability,
    DpmOutcomeReviewSupportability,
    DpmPmOperatingQualitySupportability,
)
from app.services.dpm_command_center_supportability import safe_optional_str

PM_QUALITY_SUMMARY_FORBIDDEN_ACTIONS = [
    "rank_portfolio_managers",
    "make_hr_decisions",
    "make_compensation_decisions",
    "enforce_conduct_action",
    "approve_rebalance",
    "contact_client",
    "place_orders",
    "invent_missing_evidence",
]
PM_QUALITY_SUMMARY_UNSUPPORTED_CLAIMS = [
    "pm_ranking",
    "hr_decision",
    "compensation_decision",
    "conduct_enforcement",
    "client_message",
    "trade_approval",
    "execution_instruction",
    "oms_acknowledgement",
]


def pm_quality_score_run_from(payload: dict[str, Any]) -> dict[str, object] | None:
    score_run = payload.get("score_run")
    if isinstance(score_run, dict):
        return score_run
    if payload.get("score_run_id") is not None:
        return payload
    return None


def pm_quality_summary_source_refs(score_run: dict[str, object]) -> list[str]:
    refs: list[str] = []
    source_refs = score_run.get("source_refs")
    if isinstance(source_refs, list):
        for item in source_refs:
            ref = _source_ref_label(item)
            if ref is not None:
                refs.append(ref)

    score_run_id = safe_optional_str(score_run.get("score_run_id"))
    if score_run_id is not None:
        refs.append(f"lotus-manage:pm-quality-score-run:{score_run_id}")
    policy_id = safe_optional_str(score_run.get("policy_id"))
    policy_version = safe_optional_str(score_run.get("policy_version"))
    if policy_id is not None and policy_version is not None:
        refs.append(f"lotus-manage:pm-quality-policy:{policy_id}:{policy_version}")

    return sorted(set(refs))


def find_exception(payload: dict[str, Any], exception_id: str) -> dict[str, Any] | None:
    items = payload.get("items")
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("exception_id") == exception_id:
            return item
    return None


def exception_summary_input_from_exception(exception: dict[str, Any]) -> dict[str, object]:
    exception_id = str(exception.get("exception_id") or "")
    portfolio_id = str(exception.get("portfolio_id") or "")
    content_hash = _content_hash(
        {
            "exception_id": exception_id,
            "portfolio_id": portfolio_id,
            "state": exception.get("state"),
            "severity": exception.get("severity"),
            "reason_code": exception.get("reason_code"),
            "recommended_action": exception.get("recommended_action"),
            "source_lineage": exception.get("source_lineage"),
        }
    )
    source_refs = _bounded_exception_source_refs(exception, content_hash)
    bounded_exception = {
        "exception_id": exception_id,
        "portfolio_id": portfolio_id,
        "mandate_id": safe_optional_str(exception.get("mandate_id")) or "",
        "severity": str(exception.get("severity") or "UNKNOWN"),
        "state": str(exception.get("state") or "UNKNOWN"),
        "reason_code": str(exception.get("reason_code") or "UNKNOWN"),
        "recommended_action": str(exception.get("recommended_action") or "REVIEW_WITH_PM"),
        "detected_at": safe_optional_str(exception.get("detected_at")) or "",
        "source_refs": source_refs,
    }
    evidence_ref = {
        "source_system": "lotus-manage",
        "source_type": "DPM_EXCEPTION_SUMMARY_INPUT",
        "source_id": f"{portfolio_id}:dpm_exception_summary_input:{exception_id}",
        "content_hash": content_hash,
    }
    return {
        "contract_version": "1.0",
        "portfolio_id": portfolio_id,
        "mandate_id": bounded_exception["mandate_id"],
        "as_of_date": safe_optional_str(exception.get("as_of_date")) or "",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "exception_count": 1,
        "exceptions": [bounded_exception],
        "source_refs": [evidence_ref],
        "redaction_policy": "NO_RAW_PAYLOADS",
        "evidence_ref": evidence_ref,
        "content_hash": content_hash,
    }


def exception_summary_source_refs(exception_summary_input: dict[str, object]) -> list[str]:
    refs = [f"lotus-manage:exception-summary:{exception_summary_input['content_hash']}"]
    exceptions = exception_summary_input.get("exceptions")
    if isinstance(exceptions, list):
        for item in exceptions:
            if isinstance(item, dict):
                exception_id = item.get("exception_id")
                if exception_id:
                    refs.append(f"lotus-manage:monitoring-exception:{exception_id}")
    return sorted(set(refs))


def outcome_ai_source_refs(payload: dict[str, Any], outcome_review_id: str) -> list[str]:
    source_refs: list[str] = [f"lotus-manage:outcome-review:{outcome_review_id}"]
    evidence_ref = payload.get("evidence_ref")
    if isinstance(evidence_ref, dict):
        source_id = evidence_ref.get("source_id")
        if source_id is not None:
            source_refs.append(f"lotus-manage:outcome-ai-evidence:{source_id}")
    if len(source_refs) == 1:
        source_refs.append(f"lotus-manage:outcome-ai-evidence:{outcome_review_id}")
    return source_refs


def exception_summary_task_payload(
    *,
    exception_summary_input: dict[str, object],
    summary_request: dict[str, object],
    supportability: DpmCommandCenterSupportability,
) -> dict[str, object]:
    return {
        "exception_summary_input": exception_summary_input,
        "exception_summary_request": summary_request,
        "supportability": {
            "source_state": supportability.state,
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
        },
    }


def outcome_review_narrative_task_payload(
    *,
    ai_evidence_input: dict[str, Any],
    narrative_request: dict[str, object],
    supportability: DpmOutcomeReviewSupportability,
) -> dict[str, object]:
    return {
        "ai_evidence_input": ai_evidence_input,
        "narrative_request": narrative_request,
        "supportability": {
            "source_state": supportability.state,
            "reason_codes": supportability.reason_codes,
            "blocked_actions": supportability.blocked_actions,
            "requires_human_review": True,
            "unsupported_claims": [
                "client_contact",
                "trade_approval",
                "portfolio_manager_scoring",
            ],
        },
    }


def pm_quality_summary_task_payload(
    *,
    manage_payload: dict[str, Any],
    score_run: dict[str, object],
    summary_request: dict[str, object],
    supportability: DpmPmOperatingQualitySupportability,
) -> dict[str, object]:
    task_payload: dict[str, object] = {
        "score_run": score_run,
        "summary_request": summary_request,
        "supportability": {
            "source_state": supportability.state,
            "requires_human_review": True,
            "forbidden_actions": PM_QUALITY_SUMMARY_FORBIDDEN_ACTIONS,
            "unsupported_claims": PM_QUALITY_SUMMARY_UNSUPPORTED_CLAIMS,
        },
    }
    portfolio_memory_context = manage_payload.get("portfolio_memory_context")
    if isinstance(portfolio_memory_context, dict):
        task_payload["portfolio_memory_context"] = portfolio_memory_context
    return task_payload


def workflow_pack_task_request(
    *,
    correlation_id: str,
    summary: str,
    payload: dict[str, object],
    source_refs: list[str],
) -> dict[str, object]:
    return {
        "task_id": "explain.v1",
        "input_mode": "STRUCTURED_CONTEXT",
        "caller": {
            "caller_app": "lotus-gateway",
            "correlation_id": correlation_id,
        },
        "context": {
            "summary": summary,
            "payload": payload,
            "source_refs": source_refs,
        },
        "expected_output_label": "EXPLANATION_ONLY",
    }


def _source_ref_label(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None
    source_system = value.get("source_system") or value.get("sourceSystem") or "lotus-manage"
    source_type = value.get("source_type") or value.get("sourceType") or value.get("product_name")
    source_id = value.get("source_id") or value.get("sourceId")
    if source_type is None or source_id is None:
        return None
    return f"{source_system}:{source_type}:{source_id}"


def _bounded_exception_source_refs(
    exception: dict[str, Any],
    content_hash: str,
) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = [
        {
            "source_system": "lotus-manage",
            "source_type": "DPM_MONITORING_EXCEPTION",
            "source_id": str(exception.get("exception_id") or ""),
            "content_hash": content_hash,
        }
    ]
    source_lineage = exception.get("source_lineage")
    if isinstance(source_lineage, list):
        for index, item in enumerate(source_lineage):
            if isinstance(item, dict):
                source_system = item.get("source_system") or item.get("sourceSystem")
                source_type = item.get("source_type") or item.get("product_name")
                source_id = item.get("source_id") or item.get("product_version") or index
                if source_system and source_type:
                    refs.append(
                        {
                            "source_system": str(source_system),
                            "source_type": str(source_type),
                            "source_id": str(source_id),
                            "content_hash": safe_optional_str(item.get("content_hash"))
                            or content_hash,
                        }
                    )
    return refs


def _content_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
