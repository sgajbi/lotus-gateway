"""State derivation for platform shell workspace descriptors."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkspaceDescriptorState:
    supportability_state: str
    evidence_state: str
    freshness_state: str
    reasons: list[str]


def workspace_descriptor_state(
    *,
    workspace_id: str,
    enabled: bool,
    dependency_source: str,
    source_supportability: dict[str, Any] | None,
    source_health: str,
) -> WorkspaceDescriptorState:
    if enabled and source_health == "available":
        descriptor_state = WorkspaceDescriptorState(
            supportability_state="ready",
            evidence_state="source_backed",
            freshness_state="current",
            reasons=[],
        )
    elif source_health == "unavailable":
        descriptor_state = WorkspaceDescriptorState(
            supportability_state="partial",
            evidence_state="partial",
            freshness_state="partial",
            reasons=[f"{dependency_source}_unavailable"],
        )
    else:
        reason = f"{workspace_id}_disabled" if not enabled else f"{dependency_source}_unknown"
        descriptor_state = WorkspaceDescriptorState(
            supportability_state="unavailable",
            evidence_state="unavailable",
            freshness_state="unavailable",
            reasons=[reason],
        )
    return apply_source_supportability(
        descriptor_state=descriptor_state,
        source_health=source_health,
        source_supportability=source_supportability,
    )


def apply_source_supportability(
    *,
    descriptor_state: WorkspaceDescriptorState,
    source_health: str,
    source_supportability: dict[str, Any] | None,
) -> WorkspaceDescriptorState:
    if source_supportability is None or source_health != "available":
        return descriptor_state
    source_reason = source_supportability.get("reason")
    return WorkspaceDescriptorState(
        supportability_state=str(
            source_supportability.get("state") or descriptor_state.supportability_state
        ),
        evidence_state=descriptor_state.evidence_state,
        freshness_state=descriptor_state.freshness_state,
        reasons=[str(source_reason)] if source_reason else descriptor_state.reasons,
    )


def source_supportability(
    *,
    sources: dict[str, dict[str, Any]],
    source_name: str,
) -> dict[str, Any] | None:
    supportability = sources.get(source_name, {}).get("supportability")
    if not isinstance(supportability, dict):
        return None
    return supportability
