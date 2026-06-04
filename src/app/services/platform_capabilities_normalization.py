from typing import Any

from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformBootstrapCaching,
    PlatformBootstrapEvidence,
    PlatformBootstrapFreshness,
    PlatformBootstrapSupportability,
    PlatformBootstrapVersioning,
    PlatformCapabilitiesNormalized,
    PlatformShellBootstrap,
    PlatformShellWorkspaceDescriptor,
)

SHELL_BOOTSTRAP_CONTRACT_VERSION = "shell-bootstrap.v1"
PRIMARY_CAPABILITY_SOURCES = (
    "lotus_core",
    "lotus_performance",
    "lotus_advise",
    "lotus_manage",
    "lotus_report",
)
OPTIONAL_CAPABILITY_SOURCES = ("lotus_risk",)
RISK_ANALYTICS_FEATURE_KEYS = (
    "risk.analytics.risk_analytics",
    "risk.analytics.drawdown",
    "risk.analytics.concentration",
    "risk.analytics.rolling_metrics",
    "risk.analytics.historical_attribution",
    "risk.analytics.metrics",
)


def build_normalized_capabilities(
    *,
    sources: dict[str, dict[str, Any]],
    errors: list[CapabilitySourceError],
    lotus_core_policy: dict[str, Any] | None,
    evaluated_at: str,
    contract_version: str,
) -> PlatformCapabilitiesNormalized:
    input_modes_by_source, input_modes_union, policy_versions_by_source = (
        source_input_modes_and_policy_versions(sources)
    )
    feature_enabled = feature_enablement(sources)
    health = module_health(sources=sources, errors=errors)
    navigation = navigation_flags(feature_enabled)
    workflows = workflow_flags(sources)
    policy_diagnostics = lotus_core_policy_diagnostics(
        lotus_core_policy=lotus_core_policy,
        errors=errors,
    )
    shell_bootstrap = build_shell_bootstrap(
        sources=sources,
        navigation=navigation,
        module_health_by_source=health,
        policy_versions_by_source=policy_versions_by_source,
        errors=errors,
        evaluated_at=evaluated_at,
        contract_version=contract_version,
    )
    return PlatformCapabilitiesNormalized(
        navigation=navigation,
        workflowFlags=workflows,
        inputModesBySource=input_modes_by_source,
        inputModesUnion=input_modes_union,
        moduleHealth=health,
        policyVersionsBySource=policy_versions_by_source,
        lotusCorePolicyDiagnostics=policy_diagnostics,
        shellBootstrap=shell_bootstrap,
    )


def source_input_modes_and_policy_versions(
    sources: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[str]], list[str], dict[str, str]]:
    input_modes_by_source: dict[str, list[str]] = {}
    input_modes_union: list[str] = []
    policy_versions_by_source: dict[str, str] = {}
    for source_name, source_payload in sources.items():
        source_modes = payload_value(
            source_payload,
            "supportedInputModes",
            "supported_input_modes",
            default=[],
        )
        normalized_modes = [str(mode) for mode in source_modes]
        input_modes_by_source[source_name] = normalized_modes
        policy_versions_by_source[source_name] = str(
            payload_value(
                source_payload,
                "policyVersion",
                "policy_version",
                default="unknown",
            )
        )
        for mode in normalized_modes:
            if mode not in input_modes_union:
                input_modes_union.append(mode)
    for source_name in (*PRIMARY_CAPABILITY_SOURCES, *OPTIONAL_CAPABILITY_SOURCES):
        policy_versions_by_source.setdefault(source_name, "unknown")
    return input_modes_by_source, input_modes_union, policy_versions_by_source


def feature_enablement(sources: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {
        "lotus_core_snapshot": feature_enabled(
            sources=sources,
            source_name="lotus_core",
            feature_keys=(
                "lotus_core.integration.core_snapshot",
                "lotus_core.support.overview_api",
                "lotus_core.ingestion.portfolio_bundle_adapter",
                "pas.integration.core_snapshot",
            ),
        ),
        "lotus_core_intake": feature_enabled(
            sources=sources,
            source_name="lotus_core",
            feature_keys=(
                "lotus_core.ingestion.bulk_upload",
                "lotus_core.ingestion.bulk_upload_adapter",
                "lotus_core.ingestion.portfolio_bundle_adapter",
                "pas.ingestion.bulk_upload",
            ),
        ),
        "lotus_performance_analytics": any(
            feature_enabled(sources=sources, source_name="lotus_performance", feature_keys=(key,))
            for key in (
                "lotus_performance.analytics.twr",
                "performance.analytics.twr",
                "lotus_performance.analytics.mwr",
                "performance.analytics.mwr",
                "lotus_performance.analytics.contribution",
                "performance.analytics.contribution",
                "lotus_performance.analytics.attribution",
                "performance.analytics.attribution",
            )
        ),
        "lotus_advise_lifecycle": feature_enabled(
            sources=sources,
            source_name="lotus_advise",
            feature_keys=(
                "advisory.proposals.lifecycle",
                "lotus_advise.proposals.lifecycle",
                "advise.proposals.lifecycle",
                "dpm.proposals.lifecycle",
            ),
        ),
        "lotus_manage_support": feature_enabled(
            sources=sources,
            source_name="lotus_manage",
            feature_keys=(
                "lotus_manage.support.run_apis",
                "dpm.support.run_apis",
            ),
        ),
        "lotus_report_reporting": any(
            feature_enabled(sources=sources, source_name="lotus_report", feature_keys=(key,))
            for key in (
                "lotus_report.reporting.portfolio_summary",
                "ras.reporting.portfolio_summary",
                "lotus_report.reporting.portfolio_review",
                "ras.reporting.portfolio_review",
                "lotus_report.aggregation.portfolio_snapshot",
                "ras.aggregation.portfolio_snapshot",
            )
        ),
        "lotus_risk_analytics": any(
            feature_enabled(sources=sources, source_name="lotus_risk", feature_keys=(key,))
            for key in RISK_ANALYTICS_FEATURE_KEYS
        ),
    }


def navigation_flags(feature_enabled_by_key: dict[str, bool]) -> dict[str, bool]:
    core_available = (
        feature_enabled_by_key["lotus_core_intake"] or feature_enabled_by_key["lotus_core_snapshot"]
    )
    return {
        "command_center": True,
        "portfolio_intake": core_available,
        "analytics_studio": feature_enabled_by_key["lotus_performance_analytics"],
        "advisory_pipeline": feature_enabled_by_key["lotus_advise_lifecycle"],
        "scenario_builder": feature_enabled_by_key["lotus_advise_lifecycle"],
        "decision_console": (
            feature_enabled_by_key["lotus_core_snapshot"]
            and (
                feature_enabled_by_key["lotus_advise_lifecycle"]
                or feature_enabled_by_key["lotus_manage_support"]
            )
        ),
        "reporting_hub": feature_enabled_by_key["lotus_report_reporting"],
        "portfolio_workspace": core_available,
        "performance_workspace": feature_enabled_by_key["lotus_performance_analytics"],
        "risk_workspace": feature_enabled_by_key["lotus_risk_analytics"],
        "proposal_workspace": feature_enabled_by_key["lotus_advise_lifecycle"],
        "advisory_workspace": feature_enabled_by_key["lotus_advise_lifecycle"],
    }


def workflow_flags(sources: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {
        "proposal_lifecycle": any_workflow_enabled(
            sources=sources,
            source_name="lotus_advise",
            workflow_keys=(
                "advisory_proposal_lifecycle",
                "proposal_lifecycle",
            ),
        ),
        "proposal_approval_flow": any_workflow_enabled(
            sources=sources,
            source_name="lotus_advise",
            workflow_keys=(
                "advisory_proposal_approval_flow",
                "proposal_approval_flow",
            ),
        ),
        "portfolio_bulk_onboarding": workflow_enabled(
            sources=sources,
            source_name="lotus_core",
            workflow_key="portfolio_bulk_onboarding",
        ),
        "performance_snapshot": workflow_enabled(
            sources=sources,
            source_name="lotus_performance",
            workflow_key="performance_snapshot",
        ),
        "portfolio_reporting": workflow_enabled(
            sources=sources,
            source_name="lotus_report",
            workflow_key="portfolio_reporting",
        ),
    }


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


def feature_enabled(
    *,
    sources: dict[str, dict[str, Any]],
    source_name: str,
    feature_keys: tuple[str, ...],
) -> bool:
    source_payload = sources.get(source_name, {})
    features = source_payload.get("features", [])
    if not isinstance(features, list):
        return False
    for feature in features:
        if not isinstance(feature, dict):
            continue
        if str(feature.get("key")) in feature_keys:
            return bool(feature.get("enabled"))
    return False


def payload_value(
    payload: dict[str, Any],
    camel_key: str,
    snake_key: str,
    *,
    default: Any,
) -> Any:
    value = payload.get(camel_key, payload.get(snake_key, default))
    if isinstance(default, list) and not isinstance(value, list):
        return []
    return value


def workflow_enabled(
    *,
    sources: dict[str, dict[str, Any]],
    source_name: str,
    workflow_key: str,
) -> bool:
    source_payload = sources.get(source_name, {})
    workflows = source_payload.get("workflows", [])
    if not isinstance(workflows, list):
        return False
    for workflow in workflows:
        if not isinstance(workflow, dict):
            continue
        if str(workflow.get("workflow_key")) == workflow_key:
            return bool(workflow.get("enabled"))
    return False


def any_workflow_enabled(
    *,
    sources: dict[str, dict[str, Any]],
    source_name: str,
    workflow_keys: tuple[str, ...],
) -> bool:
    return any(
        workflow_enabled(
            sources=sources,
            source_name=source_name,
            workflow_key=workflow_key,
        )
        for workflow_key in workflow_keys
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


def module_health(
    *,
    sources: dict[str, dict[str, Any]],
    errors: list[CapabilitySourceError],
) -> dict[str, str]:
    errored_sources = {error.service for error in errors}
    health: dict[str, str] = {}
    for source_name in (*PRIMARY_CAPABILITY_SOURCES, *OPTIONAL_CAPABILITY_SOURCES):
        if source_name in sources:
            health[source_name] = "available"
        elif source_name in errored_sources:
            health[source_name] = "unavailable"
        else:
            health[source_name] = "unknown"
    return health


def lotus_core_policy_diagnostics(
    *,
    lotus_core_policy: dict[str, Any] | None,
    errors: list[CapabilitySourceError],
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "available": False,
        "allowedSections": [],
        "warnings": [],
        "policyProvenance": {
            "policyVersion": "unknown",
            "policySource": "unknown",
            "matchedRuleId": "unknown",
            "strictMode": False,
        },
    }

    if lotus_core_policy is not None:
        diagnostics["available"] = True
        allowed_sections = lotus_core_policy.get("allowedSections", [])
        warnings = lotus_core_policy.get("warnings", [])
        provenance = lotus_core_policy.get("policyProvenance", {})
        diagnostics["allowedSections"] = (
            [str(section) for section in allowed_sections]
            if isinstance(allowed_sections, list)
            else []
        )
        diagnostics["warnings"] = (
            [str(warning) for warning in warnings] if isinstance(warnings, list) else []
        )
        if isinstance(provenance, dict):
            diagnostics["policyProvenance"] = {
                "policyVersion": str(provenance.get("policyVersion", "unknown")),
                "policySource": str(provenance.get("policySource", "unknown")),
                "matchedRuleId": str(provenance.get("matchedRuleId", "unknown")),
                "strictMode": bool(provenance.get("strictMode", False)),
            }

    if any(error.service == "lotus_core_policy" for error in errors):
        diagnostics["warnings"] = list(diagnostics["warnings"]) + [
            "LOTUS_CORE_POLICY_ENDPOINT_UNAVAILABLE"
        ]
    return diagnostics
