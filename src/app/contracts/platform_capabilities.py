from typing import Any

from pydantic import BaseModel, Field

from app.contracts.platform_capabilities_bootstrap import (
    PlatformBootstrapCaching,
    PlatformBootstrapEvidence,
    PlatformBootstrapFreshness,
    PlatformBootstrapSupportability,
    PlatformBootstrapVersioning,
    PlatformShellBootstrap,
    PlatformShellWorkspaceDescriptor,
)

__all__ = [
    "CapabilitySourceError",
    "PlatformBootstrapCaching",
    "PlatformBootstrapEvidence",
    "PlatformBootstrapFreshness",
    "PlatformBootstrapSupportability",
    "PlatformBootstrapVersioning",
    "PlatformCapabilitiesData",
    "PlatformCapabilitiesNormalized",
    "PlatformCapabilitiesResponse",
    "PlatformShellBootstrap",
    "PlatformShellWorkspaceDescriptor",
]


class CapabilitySourceError(BaseModel):
    service: str = Field(
        description="Gateway source key for the upstream service or policy dependency.",
        examples=["lotus_performance"],
    )
    status_code: int = Field(
        description="HTTP status or synthesized upstream failure status captured by gateway.",
        examples=[503],
    )
    detail: str = Field(
        description="Normalized upstream failure detail preserved for partial-failure diagnostics.",
        examples=["upstream failed"],
    )


class PlatformCapabilitiesNormalized(BaseModel):
    navigation: dict[str, bool] = Field(
        description="Gateway navigation toggles derived from upstream capability truth.",
        examples=[{"performance_workspace": True, "risk_workspace": False}],
    )
    workflow_flags: dict[str, bool] = Field(
        alias="workflowFlags",
        description="Normalized workflow enablement flags for platform surfaces.",
        examples=[{"proposal_lifecycle": True}],
    )
    input_modes_by_source: dict[str, list[str]] = Field(
        alias="inputModesBySource",
        description="Published input modes keyed by gateway source name.",
        examples=[{"lotus_core": ["pas_ref"], "lotus_performance": ["pas_ref", "inline_bundle"]}],
    )
    input_modes_union: list[str] = Field(
        alias="inputModesUnion",
        description="Union of published upstream input modes across sources.",
        examples=[["pas_ref", "inline_bundle"]],
    )
    module_health: dict[str, str] = Field(
        alias="moduleHealth",
        description="Gateway health classification per normalized source.",
        examples=[
            {
                "lotus_core": "available",
                "lotus_performance": "available",
                "lotus_risk": "unavailable",
            }
        ],
    )
    policy_versions_by_source: dict[str, str] = Field(
        alias="policyVersionsBySource",
        description="Policy versions keyed by normalized gateway source.",
        examples=[
            {
                "lotus_core": "pas-v3",
                "lotus_performance": "lotus-performance-v4",
                "lotus_risk": "risk-v2",
            }
        ],
    )
    lotus_core_policy_diagnostics: dict[str, Any] = Field(
        alias="lotusCorePolicyDiagnostics",
        description="Normalized lotus-core policy diagnostics used by shell and workspaces.",
        examples=[
            {
                "available": True,
                "allowedSections": ["OVERVIEW"],
                "warnings": [],
                "policyProvenance": {
                    "policyVersion": "pas-policy-v7",
                    "policySource": "tenant",
                    "matchedRuleId": "tenant.default.consumers.lotus-gateway",
                    "strictMode": True,
                },
            }
        ],
    )
    shell_bootstrap: PlatformShellBootstrap = Field(
        alias="shellBootstrap",
        description="Normalized shell bootstrap contract for navigation and workspace gating.",
    )

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesData(BaseModel):
    consumer_system: str = Field(
        alias="consumerSystem",
        description="Gateway consumer identity requested by the caller.",
        examples=["lotus-gateway", "lotus-workbench"],
    )
    tenant_id: str = Field(
        alias="tenantId",
        description="Gateway tenant scope requested by the caller.",
        examples=["default", "tenant-a"],
    )
    contract_version: str = Field(
        alias="contractVersion",
        description="Gateway platform-capabilities contract version.",
        examples=["v1"],
    )
    sources: dict[str, dict[str, Any]] = Field(
        description="Raw upstream capability payloads keyed by normalized gateway source name.",
        examples=[
            {
                "lotus_core": {"sourceService": "lotus-core", "policyVersion": "pas-v3"},
                "lotus_performance": {
                    "sourceService": "lotus-performance",
                    "policyVersion": "lotus-performance-v4",
                },
                "lotus_risk": {
                    "sourceService": "lotus-risk",
                    "policyVersion": "risk-v2",
                },
            }
        ],
    )
    partial_failure: bool = Field(
        alias="partialFailure",
        description=(
            "Whether one or more upstream sources failed while gateway composed the response."
        ),
        examples=[False],
    )
    errors: list[CapabilitySourceError] = Field(
        default_factory=list,
        description="Upstream failures preserved for UI and operator diagnostics.",
    )
    normalized: PlatformCapabilitiesNormalized = Field(
        description="Normalized capability contract used by shell and workspace consumers."
    )

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesResponse(BaseModel):
    data: PlatformCapabilitiesData = Field(
        description="Platform capability envelope used by Workbench shell and workspace gating."
    )
