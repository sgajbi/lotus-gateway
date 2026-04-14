from typing import Any

from pydantic import BaseModel, Field


class CapabilitySourceError(BaseModel):
    service: str
    status_code: int
    detail: str


class PlatformBootstrapSupportability(BaseModel):
    state: str
    reasons: list[str] = Field(default_factory=list)


class PlatformBootstrapFreshness(BaseModel):
    state: str
    freshness_class: str = Field(alias="freshnessClass")
    evaluated_at: str = Field(alias="evaluatedAt")
    max_age_seconds: int | None = Field(default=None, alias="maxAgeSeconds")

    model_config = {"populate_by_name": True}


class PlatformBootstrapEvidence(BaseModel):
    state: str
    lineage_sources: list[str] = Field(default_factory=list, alias="lineageSources")
    partial_failure: bool = Field(alias="partialFailure")
    source_error_services: list[str] = Field(default_factory=list, alias="sourceErrorServices")

    model_config = {"populate_by_name": True}


class PlatformBootstrapVersioning(BaseModel):
    shell_contract_version: str = Field(alias="shellContractVersion")
    capability_contract_version: str = Field(alias="capabilityContractVersion")
    source_policy_version: str | None = Field(default=None, alias="sourcePolicyVersion")
    source_policy_versions: dict[str, str] = Field(
        default_factory=dict,
        alias="sourcePolicyVersions",
    )

    model_config = {"populate_by_name": True}


class PlatformBootstrapCaching(BaseModel):
    cache_mode: str = Field(alias="cacheMode")
    invalidation_owner: str = Field(alias="invalidationOwner")
    stale_read_tolerance: str = Field(alias="staleReadTolerance")
    revalidate_on_navigation: bool = Field(alias="revalidateOnNavigation")
    ttl_seconds: int | None = Field(default=None, alias="ttlSeconds")
    correctness_critical: bool = Field(alias="correctnessCritical")

    model_config = {"populate_by_name": True}


class PlatformShellWorkspaceDescriptor(BaseModel):
    id: str
    label: str
    href: str
    enabled: bool
    supportability: PlatformBootstrapSupportability
    freshness: PlatformBootstrapFreshness
    evidence: PlatformBootstrapEvidence
    versioning: PlatformBootstrapVersioning
    caching: PlatformBootstrapCaching


class PlatformShellBootstrap(BaseModel):
    contract_version: str = Field(alias="contractVersion")
    supportability: PlatformBootstrapSupportability
    freshness: PlatformBootstrapFreshness
    evidence: PlatformBootstrapEvidence
    versioning: PlatformBootstrapVersioning
    caching: PlatformBootstrapCaching
    workspaces: list[PlatformShellWorkspaceDescriptor]

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesNormalized(BaseModel):
    navigation: dict[str, bool]
    workflow_flags: dict[str, bool] = Field(alias="workflowFlags")
    input_modes_by_source: dict[str, list[str]] = Field(alias="inputModesBySource")
    input_modes_union: list[str] = Field(alias="inputModesUnion")
    module_health: dict[str, str] = Field(alias="moduleHealth")
    policy_versions_by_source: dict[str, str] = Field(alias="policyVersionsBySource")
    lotus_core_policy_diagnostics: dict[str, Any] = Field(alias="lotusCorePolicyDiagnostics")
    shell_bootstrap: PlatformShellBootstrap = Field(alias="shellBootstrap")

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesData(BaseModel):
    consumer_system: str = Field(alias="consumerSystem")
    tenant_id: str = Field(alias="tenantId")
    contract_version: str = Field(alias="contractVersion")
    sources: dict[str, dict[str, Any]]
    partial_failure: bool = Field(alias="partialFailure")
    errors: list[CapabilitySourceError] = Field(default_factory=list)
    normalized: PlatformCapabilitiesNormalized

    model_config = {"populate_by_name": True}


class PlatformCapabilitiesResponse(BaseModel):
    data: PlatformCapabilitiesData
