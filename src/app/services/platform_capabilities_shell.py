from typing import Any

from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformBootstrapCaching,
    PlatformBootstrapEvidence,
    PlatformBootstrapFreshness,
    PlatformBootstrapSupportability,
    PlatformBootstrapVersioning,
    PlatformShellBootstrap,
)
from app.services.platform_capabilities_workspace_descriptors import (
    SHELL_BOOTSTRAP_CONTRACT_VERSION,
    build_workspace_descriptor,
    workspace_descriptors,
)

__all__ = [
    "build_shell_bootstrap",
    "build_workspace_descriptor",
]


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

    return PlatformShellBootstrap(
        contractVersion=SHELL_BOOTSTRAP_CONTRACT_VERSION,
        supportability=shell_supportability(errors=errors),
        freshness=shell_freshness(errors=errors, evaluated_at=evaluated_at),
        evidence=shell_evidence(
            errors=errors,
            error_services=error_services,
            policy_versions_by_source=policy_versions_by_source,
        ),
        versioning=shell_versioning(
            contract_version=contract_version,
            policy_versions_by_source=policy_versions_by_source,
        ),
        caching=shell_caching(),
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


def shell_supportability(
    *,
    errors: list[CapabilitySourceError],
) -> PlatformBootstrapSupportability:
    return PlatformBootstrapSupportability(
        state="partial" if errors else "ready",
        reasons=[f"{error.service}:{error.status_code}" for error in errors],
    )


def shell_freshness(
    *,
    errors: list[CapabilitySourceError],
    evaluated_at: str,
) -> PlatformBootstrapFreshness:
    return PlatformBootstrapFreshness(
        state="current" if not errors else "partial",
        freshnessClass="shell_navigation",
        evaluatedAt=evaluated_at,
        maxAgeSeconds=60,
    )


def shell_evidence(
    *,
    errors: list[CapabilitySourceError],
    error_services: list[str],
    policy_versions_by_source: dict[str, str],
) -> PlatformBootstrapEvidence:
    return PlatformBootstrapEvidence(
        state="partial" if errors else "source_backed",
        lineageSources=list(policy_versions_by_source.keys()),
        partialFailure=bool(errors),
        sourceErrorServices=error_services,
    )


def shell_versioning(
    *,
    contract_version: str,
    policy_versions_by_source: dict[str, str],
) -> PlatformBootstrapVersioning:
    return PlatformBootstrapVersioning(
        shellContractVersion=SHELL_BOOTSTRAP_CONTRACT_VERSION,
        capabilityContractVersion=contract_version,
        sourcePolicyVersions=policy_versions_by_source,
    )


def shell_caching() -> PlatformBootstrapCaching:
    return PlatformBootstrapCaching(
        cacheMode="request_scoped_composition",
        invalidationOwner="upstream_service",
        staleReadTolerance="bounded_navigation_refresh",
        revalidateOnNavigation=True,
        ttlSeconds=60,
        correctnessCritical=False,
    )
