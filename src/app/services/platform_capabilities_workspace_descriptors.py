from dataclasses import dataclass
from typing import Any

from app.contracts.platform_capabilities import (
    PlatformBootstrapCaching,
    PlatformBootstrapEvidence,
    PlatformBootstrapFreshness,
    PlatformBootstrapSupportability,
    PlatformBootstrapVersioning,
    PlatformShellWorkspaceDescriptor,
)

SHELL_BOOTSTRAP_CONTRACT_VERSION = "shell-bootstrap.v1"


@dataclass(frozen=True)
class WorkspaceDescriptorSpec:
    workspace_id: str
    label: str
    href: str
    navigation_key: str
    dependency_source: str
    freshness_class: str
    max_age_seconds: int
    cache_mode: str
    stale_read_tolerance: str
    source_supportability_source: str | None = None


@dataclass(frozen=True)
class WorkspaceDescriptorState:
    supportability_state: str
    evidence_state: str
    freshness_state: str
    reasons: list[str]


WORKSPACE_DESCRIPTOR_SPECS = (
    WorkspaceDescriptorSpec(
        workspace_id="portfolio",
        label="Portfolio",
        href="/portfolio",
        navigation_key="portfolio_workspace",
        dependency_source="lotus_core",
        freshness_class="shell_navigation",
        max_age_seconds=60,
        cache_mode="request_scoped_composition",
        stale_read_tolerance="bounded_navigation_refresh",
    ),
    WorkspaceDescriptorSpec(
        workspace_id="performance",
        label="Performance",
        href="/performance",
        navigation_key="performance_workspace",
        dependency_source="lotus_performance",
        freshness_class="analytical_summary",
        max_age_seconds=120,
        cache_mode="short_lived_revalidation",
        stale_read_tolerance="bounded_analytical_read",
    ),
    WorkspaceDescriptorSpec(
        workspace_id="risk",
        label="Risk",
        href="/performance?mode=risk",
        navigation_key="risk_workspace",
        dependency_source="lotus_risk",
        freshness_class="analytical_summary",
        max_age_seconds=120,
        cache_mode="short_lived_revalidation",
        stale_read_tolerance="bounded_analytical_read",
    ),
    WorkspaceDescriptorSpec(
        workspace_id="proposal",
        label="Proposal",
        href="/proposals",
        navigation_key="proposal_workspace",
        dependency_source="lotus_advise",
        freshness_class="workflow_truth",
        max_age_seconds=0,
        cache_mode="authoritative_read",
        stale_read_tolerance="none",
        source_supportability_source="lotus_advise",
    ),
    WorkspaceDescriptorSpec(
        workspace_id="advisory",
        label="Advisory",
        href="/recommendations",
        navigation_key="advisory_workspace",
        dependency_source="lotus_advise",
        freshness_class="workflow_truth",
        max_age_seconds=0,
        cache_mode="authoritative_read",
        stale_read_tolerance="none",
        source_supportability_source="lotus_advise",
    ),
)


def workspace_descriptors(
    *,
    sources: dict[str, dict[str, Any]],
    navigation: dict[str, bool],
    module_health_by_source: dict[str, str],
    policy_versions_by_source: dict[str, str],
    error_services: list[str],
    evaluated_at: str,
    contract_version: str,
) -> list[PlatformShellWorkspaceDescriptor]:
    return [
        build_workspace_descriptor_from_spec(
            spec=spec,
            sources=sources,
            navigation=navigation,
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
        )
        for spec in WORKSPACE_DESCRIPTOR_SPECS
    ]


def build_workspace_descriptor_from_spec(
    *,
    spec: WorkspaceDescriptorSpec,
    sources: dict[str, dict[str, Any]],
    navigation: dict[str, bool],
    module_health_by_source: dict[str, str],
    policy_versions_by_source: dict[str, str],
    error_services: list[str],
    evaluated_at: str,
    contract_version: str,
) -> PlatformShellWorkspaceDescriptor:
    return build_workspace_descriptor(
        workspace_id=spec.workspace_id,
        label=spec.label,
        href=spec.href,
        enabled=navigation[spec.navigation_key],
        dependency_source=spec.dependency_source,
        source_supportability=(
            source_supportability(
                sources=sources,
                source_name=spec.source_supportability_source,
            )
            if spec.source_supportability_source is not None
            else None
        ),
        module_health_by_source=module_health_by_source,
        policy_versions_by_source=policy_versions_by_source,
        error_services=error_services,
        evaluated_at=evaluated_at,
        contract_version=contract_version,
        freshness_class=spec.freshness_class,
        max_age_seconds=spec.max_age_seconds,
        cache_mode=spec.cache_mode,
        stale_read_tolerance=spec.stale_read_tolerance,
    )


def build_workspace_descriptor(
    *,
    workspace_id: str,
    label: str,
    href: str,
    enabled: bool,
    dependency_source: str,
    source_supportability: dict[str, Any] | None,
    module_health_by_source: dict[str, str],
    policy_versions_by_source: dict[str, str],
    error_services: list[str],
    evaluated_at: str,
    contract_version: str,
    freshness_class: str,
    max_age_seconds: int,
    cache_mode: str,
    stale_read_tolerance: str,
) -> PlatformShellWorkspaceDescriptor:
    descriptor_state = workspace_descriptor_state(
        workspace_id=workspace_id,
        enabled=enabled,
        dependency_source=dependency_source,
        source_supportability=source_supportability,
        source_health=module_health_by_source.get(dependency_source, "unknown"),
    )

    return _build_workspace_descriptor_contract(
        workspace_id=workspace_id,
        label=label,
        href=href,
        enabled=enabled,
        dependency_source=dependency_source,
        descriptor_state=descriptor_state,
        policy_versions_by_source=policy_versions_by_source,
        error_services=error_services,
        evaluated_at=evaluated_at,
        contract_version=contract_version,
        freshness_class=freshness_class,
        max_age_seconds=max_age_seconds,
        cache_mode=cache_mode,
        stale_read_tolerance=stale_read_tolerance,
    )


def _build_workspace_descriptor_contract(
    *,
    workspace_id: str,
    label: str,
    href: str,
    enabled: bool,
    dependency_source: str,
    descriptor_state: WorkspaceDescriptorState,
    policy_versions_by_source: dict[str, str],
    error_services: list[str],
    evaluated_at: str,
    contract_version: str,
    freshness_class: str,
    max_age_seconds: int,
    cache_mode: str,
    stale_read_tolerance: str,
) -> PlatformShellWorkspaceDescriptor:
    return PlatformShellWorkspaceDescriptor(
        id=workspace_id,
        label=label,
        href=href,
        enabled=enabled,
        supportability=workspace_supportability(descriptor_state=descriptor_state),
        freshness=workspace_freshness(
            descriptor_state=descriptor_state,
            freshness_class=freshness_class,
            evaluated_at=evaluated_at,
            max_age_seconds=max_age_seconds,
        ),
        evidence=workspace_evidence(
            descriptor_state=descriptor_state,
            dependency_source=dependency_source,
            error_services=error_services,
        ),
        versioning=workspace_versioning(
            dependency_source=dependency_source,
            policy_versions_by_source=policy_versions_by_source,
            contract_version=contract_version,
        ),
        caching=workspace_caching(
            dependency_source=dependency_source,
            freshness_class=freshness_class,
            max_age_seconds=max_age_seconds,
            cache_mode=cache_mode,
            stale_read_tolerance=stale_read_tolerance,
        ),
    )


def workspace_freshness(
    *,
    descriptor_state: WorkspaceDescriptorState,
    freshness_class: str,
    evaluated_at: str,
    max_age_seconds: int,
) -> PlatformBootstrapFreshness:
    return PlatformBootstrapFreshness(
        state=descriptor_state.freshness_state,
        freshnessClass=freshness_class,
        evaluatedAt=evaluated_at,
        maxAgeSeconds=max_age_seconds,
    )


def workspace_supportability(
    *,
    descriptor_state: WorkspaceDescriptorState,
) -> PlatformBootstrapSupportability:
    return PlatformBootstrapSupportability(
        state=descriptor_state.supportability_state,
        reasons=descriptor_state.reasons,
    )


def workspace_evidence(
    *,
    descriptor_state: WorkspaceDescriptorState,
    dependency_source: str,
    error_services: list[str],
) -> PlatformBootstrapEvidence:
    return PlatformBootstrapEvidence(
        state=descriptor_state.evidence_state,
        lineageSources=[dependency_source],
        partialFailure=dependency_source in error_services,
        sourceErrorServices=[dependency_source] if dependency_source in error_services else [],
    )


def workspace_versioning(
    *,
    dependency_source: str,
    policy_versions_by_source: dict[str, str],
    contract_version: str,
) -> PlatformBootstrapVersioning:
    return PlatformBootstrapVersioning(
        shellContractVersion=SHELL_BOOTSTRAP_CONTRACT_VERSION,
        capabilityContractVersion=contract_version,
        sourcePolicyVersion=policy_versions_by_source.get(dependency_source),
    )


def workspace_caching(
    *,
    dependency_source: str,
    freshness_class: str,
    max_age_seconds: int,
    cache_mode: str,
    stale_read_tolerance: str,
) -> PlatformBootstrapCaching:
    return PlatformBootstrapCaching(
        cacheMode=cache_mode,
        invalidationOwner=dependency_source,
        staleReadTolerance=stale_read_tolerance,
        revalidateOnNavigation=True,
        ttlSeconds=max_age_seconds,
        correctnessCritical=freshness_class == "workflow_truth",
    )


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
