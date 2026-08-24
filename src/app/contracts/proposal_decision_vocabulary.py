"""Validated Lotus Advise proposal-decision vocabulary consumed by Gateway."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, get_args

from app.contracts.proposal_risk_impact_allocation import (
    ProposalRiskImpactDecisionStatus,
    ProposalRiskImpactGate,
    ProposalRiskImpactGateNextStep,
    ProposalRiskImpactNextAction,
    ProposalRiskImpactTopLevelStatus,
)

SCHEMA_VERSION = "lotus.advise.proposal-decision-vocabulary.v1"
CONTRACT_VERSION = "proposal-decision-vocabulary.v1"
SOURCE_SERVICE = "lotus-advise"
EMBEDDED_RESOURCE = "lotus_advise_proposal_decision_vocabulary.v1.json"


@dataclass(frozen=True)
class ProposalDecisionVocabulary:
    """Normalized source-owned compatibility policy used by Gateway validation."""

    schema_version: str
    contract_version: str
    source_service: str
    source_authority: str
    source_rule_modules: tuple[str, ...]
    decision_status_top_levels: Mapping[str, frozenset[str]]
    decision_status_next_actions: Mapping[str, frozenset[str]]
    decision_status_workflow_gates: Mapping[str, frozenset[str]]
    workflow_gate_next_steps: Mapping[str, str]


def load_proposal_decision_vocabulary(path: Path | None = None) -> ProposalDecisionVocabulary:
    """Load and validate an embedded or caller-selected producer contract."""

    return parse_proposal_decision_vocabulary(_read_payload(path))


def parse_proposal_decision_vocabulary(
    payload: Mapping[str, Any],
) -> ProposalDecisionVocabulary:
    """Validate and normalize a decoded producer contract."""

    source_authority, source_rule_modules = _require_contract_header(payload)
    decision_rules = _require_object_list(payload, "decision_statuses")
    workflow_rules = _require_object_list(payload, "workflow_gates")
    vocabulary = ProposalDecisionVocabulary(
        schema_version=SCHEMA_VERSION,
        contract_version=CONTRACT_VERSION,
        source_service=SOURCE_SERVICE,
        source_authority=source_authority,
        source_rule_modules=source_rule_modules,
        decision_status_top_levels=_decision_mapping(decision_rules, "allowed_top_level_statuses"),
        decision_status_next_actions=_decision_mapping(
            decision_rules, "allowed_recommended_next_actions"
        ),
        decision_status_workflow_gates=_decision_mapping(decision_rules, "allowed_workflow_gates"),
        workflow_gate_next_steps=_workflow_gate_mapping(workflow_rules),
    )
    _require_typed_vocabulary_coverage(vocabulary)
    return vocabulary


def _read_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        text = resources.files("app.contracts.upstream").joinpath(EMBEDDED_RESOURCE).read_text()
    else:
        text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("proposal decision vocabulary must be a JSON object")
    return payload


def _require_contract_header(payload: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"proposal decision vocabulary schema must be {SCHEMA_VERSION}")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"proposal decision vocabulary contract must be {CONTRACT_VERSION}")
    source_owner = payload.get("source_owner")
    if not isinstance(source_owner, dict) or source_owner.get("service") != SOURCE_SERVICE:
        raise ValueError(f"proposal decision vocabulary source must be {SOURCE_SERVICE}")
    authority = _require_non_empty_string(source_owner, "authority")
    rule_modules = tuple(_require_unique_string_list(source_owner, "rule_modules"))
    return authority, rule_modules


def _require_object_list(payload: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    values = payload.get(key)
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(item, dict) for item in values)
    ):
        raise ValueError(f"proposal decision vocabulary {key} must be a non-empty object list")
    return values


def _decision_mapping(
    rules: list[dict[str, Any]],
    value_key: str,
) -> Mapping[str, frozenset[str]]:
    result: dict[str, frozenset[str]] = {}
    for rule in rules:
        status = _require_non_empty_string(rule, "status")
        if status in result:
            raise ValueError(f"duplicate proposal decision status: {status}")
        values = _require_unique_string_list(rule, value_key)
        result[status] = frozenset(values)
    return MappingProxyType(result)


def _workflow_gate_mapping(rules: list[dict[str, Any]]) -> Mapping[str, str]:
    result: dict[str, str] = {}
    for rule in rules:
        gate = _require_non_empty_string(rule, "gate")
        if gate in result:
            raise ValueError(f"duplicate proposal workflow gate: {gate}")
        result[gate] = _require_non_empty_string(rule, "recommended_next_step")
    return MappingProxyType(result)


def _require_non_empty_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"proposal decision vocabulary {key} must be a non-empty string")
    return value


def _require_unique_string_list(payload: Mapping[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(item, str) for item in values)
    ):
        raise ValueError(f"proposal decision vocabulary {key} must be a non-empty string list")
    if len(values) != len(set(values)):
        raise ValueError(f"proposal decision vocabulary {key} must not contain duplicates")
    return values


def _require_typed_vocabulary_coverage(vocabulary: ProposalDecisionVocabulary) -> None:
    _require_exact_keys(
        "decision statuses",
        vocabulary.decision_status_top_levels,
        ProposalRiskImpactDecisionStatus,
    )
    _require_exact_keys(
        "workflow gates", vocabulary.workflow_gate_next_steps, ProposalRiskImpactGate
    )
    _require_values(
        "top-level statuses",
        vocabulary.decision_status_top_levels,
        ProposalRiskImpactTopLevelStatus,
    )
    _require_values(
        "recommended actions", vocabulary.decision_status_next_actions, ProposalRiskImpactNextAction
    )
    _require_values(
        "decision workflow gates", vocabulary.decision_status_workflow_gates, ProposalRiskImpactGate
    )
    _require_values(
        "gate next steps", vocabulary.workflow_gate_next_steps, ProposalRiskImpactGateNextStep
    )


def _require_exact_keys(label: str, mapping: Mapping[str, object], literal_type: object) -> None:
    expected = {str(value) for value in get_args(literal_type)}
    actual = set(mapping)
    if actual != expected:
        raise ValueError(
            f"proposal {label} differ from Gateway types: "
            f"expected={sorted(expected)}, actual={sorted(actual)}"
        )


def _require_values(label: str, mapping: Mapping[str, object], literal_type: object) -> None:
    allowed = {str(value) for value in get_args(literal_type)}
    actual: set[str] = set()
    for value in mapping.values():
        items = value if isinstance(value, (set, frozenset)) else (value,)
        for item in items:
            if not isinstance(item, str):
                raise ValueError(f"proposal {label} must contain string values")
            actual.add(item)
    unknown = actual - allowed
    if unknown:
        raise ValueError(
            f"proposal {label} contain values absent from Gateway types: {sorted(unknown)}"
        )


__all__ = [
    "CONTRACT_VERSION",
    "EMBEDDED_RESOURCE",
    "ProposalDecisionVocabulary",
    "SCHEMA_VERSION",
    "SOURCE_SERVICE",
    "load_proposal_decision_vocabulary",
    "parse_proposal_decision_vocabulary",
]
