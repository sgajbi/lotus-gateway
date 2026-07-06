from typing import Any

from app.contracts.platform_capabilities import (
    CapabilitySourceError,
    PlatformCapabilitiesNormalized,
)
from app.services.platform_capabilities_feature_flags import (
    feature_enablement,
    workflow_flags,
)
from app.services.platform_capabilities_shell import build_shell_bootstrap

PRIMARY_CAPABILITY_SOURCES = (
    "lotus_core",
    "lotus_performance",
    "lotus_advise",
    "lotus_manage",
    "lotus_report",
)
OPTIONAL_CAPABILITY_SOURCES = ("lotus_risk",)


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


def navigation_flags(feature_enabled_by_key: dict[str, bool]) -> dict[str, bool]:
    core_available = (
        feature_enabled_by_key["lotus_core_intake"] or feature_enabled_by_key["lotus_core_snapshot"]
    )
    return {
        "command_center": feature_enabled_by_key["lotus_manage_support"],
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
