from typing import Any

from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformBootstrapCaching,
    PlatformBootstrapEvidence,
    PlatformBootstrapFreshness,
    PlatformBootstrapSupportability,
    PlatformBootstrapVersioning,
    PlatformShellBootstrap,
    PlatformShellWorkspaceDescriptor,
)

SHELL_BOOTSTRAP_CONTRACT_VERSION = "shell-bootstrap.v1"


def build_shell_bootstrap(
    *,
    sources: dict[str, dict[str, Any]],
    navigation: dict[str, bool],
    module_health_by_source: dict[str, str],
    policy_versions_by_source: dict[str, str],
    errors: list[CapabilitySourceError],
    evaluated_at: str,
    contract_version: str,
) -> PlatformShellBootstrap:
    error_services = [error.service for error in errors]
    shell_state = "partial" if errors else "ready"
    shell_reasons = [f"{error.service}:{error.status_code}" for error in errors]

    return PlatformShellBootstrap(
        contractVersion=SHELL_BOOTSTRAP_CONTRACT_VERSION,
        supportability=PlatformBootstrapSupportability(
            state=shell_state,
            reasons=shell_reasons,
        ),
        freshness=PlatformBootstrapFreshness(
            state="current" if not errors else "partial",
            freshnessClass="shell_navigation",
            evaluatedAt=evaluated_at,
            maxAgeSeconds=60,
        ),
        evidence=PlatformBootstrapEvidence(
            state="partial" if errors else "source_backed",
            lineageSources=list(policy_versions_by_source.keys()),
            partialFailure=bool(errors),
            sourceErrorServices=error_services,
        ),
        versioning=PlatformBootstrapVersioning(
            shellContractVersion=SHELL_BOOTSTRAP_CONTRACT_VERSION,
            capabilityContractVersion=contract_version,
            sourcePolicyVersions=policy_versions_by_source,
        ),
        caching=PlatformBootstrapCaching(
            cacheMode="request_scoped_composition",
            invalidationOwner="upstream_service",
            staleReadTolerance="bounded_navigation_refresh",
            revalidateOnNavigation=True,
            ttlSeconds=60,
            correctnessCritical=False,
        ),
        workspaces=workspace_descriptors(
            sources=sources,
            navigation=navigation,
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
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
        build_workspace_descriptor(
            workspace_id="portfolio",
            label="Portfolio",
            href="/portfolio",
            enabled=navigation["portfolio_workspace"],
            dependency_source="lotus_core",
            source_supportability=None,
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
            freshness_class="shell_navigation",
            max_age_seconds=60,
            cache_mode="request_scoped_composition",
            stale_read_tolerance="bounded_navigation_refresh",
        ),
        build_workspace_descriptor(
            workspace_id="performance",
            label="Performance",
            href="/performance",
            enabled=navigation["performance_workspace"],
            dependency_source="lotus_performance",
            source_supportability=None,
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
            freshness_class="analytical_summary",
            max_age_seconds=120,
            cache_mode="short_lived_revalidation",
            stale_read_tolerance="bounded_analytical_read",
        ),
        build_workspace_descriptor(
            workspace_id="risk",
            label="Risk",
            href="/performance?mode=risk",
            enabled=navigation["risk_workspace"],
            dependency_source="lotus_risk",
            source_supportability=None,
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
            freshness_class="analytical_summary",
            max_age_seconds=120,
            cache_mode="short_lived_revalidation",
            stale_read_tolerance="bounded_analytical_read",
        ),
        build_workspace_descriptor(
            workspace_id="proposal",
            label="Proposal",
            href="/proposals",
            enabled=navigation["proposal_workspace"],
            dependency_source="lotus_advise",
            source_supportability=source_supportability(
                sources=sources,
                source_name="lotus_advise",
            ),
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
            freshness_class="workflow_truth",
            max_age_seconds=0,
            cache_mode="authoritative_read",
            stale_read_tolerance="none",
        ),
        build_workspace_descriptor(
            workspace_id="advisory",
            label="Advisory",
            href="/recommendations",
            enabled=navigation["advisory_workspace"],
            dependency_source="lotus_advise",
            source_supportability=source_supportability(
                sources=sources,
                source_name="lotus_advise",
            ),
            module_health_by_source=module_health_by_source,
            policy_versions_by_source=policy_versions_by_source,
            error_services=error_services,
            evaluated_at=evaluated_at,
            contract_version=contract_version,
            freshness_class="workflow_truth",
            max_age_seconds=0,
            cache_mode="authoritative_read",
            stale_read_tolerance="none",
        ),
    ]


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
    source_health = module_health_by_source.get(dependency_source, "unknown")
    if enabled and source_health == "available":
        supportability_state = "ready"
        evidence_state = "source_backed"
        freshness_state = "current"
        reasons: list[str] = []
    elif source_health == "unavailable":
        supportability_state = "partial"
        evidence_state = "partial"
        freshness_state = "partial"
        reasons = [f"{dependency_source}_unavailable"]
    else:
        supportability_state = "unavailable"
        evidence_state = "unavailable"
        freshness_state = "unavailable"
        reasons = [f"{workspace_id}_disabled"] if not enabled else [f"{dependency_source}_unknown"]
    if source_supportability is not None and source_health == "available":
        supportability_state = str(source_supportability.get("state") or supportability_state)
        source_reason = source_supportability.get("reason")
        reasons = [str(source_reason)] if source_reason else reasons

    return PlatformShellWorkspaceDescriptor(
        id=workspace_id,
        label=label,
        href=href,
        enabled=enabled,
        supportability=PlatformBootstrapSupportability(
            state=supportability_state,
            reasons=reasons,
        ),
        freshness=PlatformBootstrapFreshness(
            state=freshness_state,
            freshnessClass=freshness_class,
            evaluatedAt=evaluated_at,
            maxAgeSeconds=max_age_seconds,
        ),
        evidence=PlatformBootstrapEvidence(
            state=evidence_state,
            lineageSources=[dependency_source],
            partialFailure=dependency_source in error_services,
            sourceErrorServices=(
                [dependency_source] if dependency_source in error_services else []
            ),
        ),
        versioning=PlatformBootstrapVersioning(
            shellContractVersion=SHELL_BOOTSTRAP_CONTRACT_VERSION,
            capabilityContractVersion=contract_version,
            sourcePolicyVersion=policy_versions_by_source.get(dependency_source),
        ),
        caching=PlatformBootstrapCaching(
            cacheMode=cache_mode,
            invalidationOwner=dependency_source,
            staleReadTolerance=stale_read_tolerance,
            revalidateOnNavigation=True,
            ttlSeconds=max_age_seconds,
            correctnessCritical=freshness_class == "workflow_truth",
        ),
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
