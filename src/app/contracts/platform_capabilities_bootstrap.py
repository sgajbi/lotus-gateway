from pydantic import BaseModel, Field


class PlatformBootstrapSupportability(BaseModel):
    state: str = Field(
        description="Supportability state for the shell or workspace surface.",
        examples=["ready"],
    )
    reasons: list[str] = Field(
        default_factory=list,
        description=(
            "Machine-readable supportability reasons when the state is partial or unavailable."
        ),
        examples=[["lotus_performance:503"]],
    )


class PlatformBootstrapFreshness(BaseModel):
    state: str = Field(
        description="Freshness state for the bootstrap payload.",
        examples=["current"],
    )
    freshness_class: str = Field(
        alias="freshnessClass",
        description="Governed freshness class for the payload slice.",
        examples=["shell_navigation"],
    )
    evaluated_at: str = Field(
        alias="evaluatedAt",
        description="UTC timestamp when gateway evaluated freshness.",
        examples=["2026-04-16T03:12:45Z"],
    )
    max_age_seconds: int | None = Field(
        default=None,
        alias="maxAgeSeconds",
        description="Maximum tolerated age in seconds before the consumer should revalidate.",
        examples=[60],
    )

    model_config = {"populate_by_name": True}


class PlatformBootstrapEvidence(BaseModel):
    state: str = Field(
        description="Evidence posture for the shell or workspace descriptor.",
        examples=["source_backed"],
    )
    lineage_sources: list[str] = Field(
        default_factory=list,
        alias="lineageSources",
        description="Upstream source keys that back the emitted contract slice.",
        examples=[["lotus_performance"]],
    )
    partial_failure: bool = Field(
        alias="partialFailure",
        description="Whether one or more contributing upstream sources failed during composition.",
        examples=[False],
    )
    source_error_services: list[str] = Field(
        default_factory=list,
        alias="sourceErrorServices",
        description="Source keys that failed while composing the payload.",
        examples=[["lotus_performance"]],
    )

    model_config = {"populate_by_name": True}


class PlatformBootstrapVersioning(BaseModel):
    shell_contract_version: str = Field(
        alias="shellContractVersion",
        description="Gateway shell-bootstrap contract version.",
        examples=["shell-bootstrap.v1"],
    )
    capability_contract_version: str = Field(
        alias="capabilityContractVersion",
        description="Gateway platform-capabilities contract version.",
        examples=["v1"],
    )
    source_policy_version: str | None = Field(
        default=None,
        alias="sourcePolicyVersion",
        description="Single-source policy version when the descriptor depends on one source.",
        examples=["lotus-performance-tenant-a-v4"],
    )
    source_policy_versions: dict[str, str] = Field(
        default_factory=dict,
        alias="sourcePolicyVersions",
        description="Source-policy versions keyed by gateway source name.",
        examples=[{"lotus_core": "pas-v3", "lotus_performance": "lotus-performance-v4"}],
    )

    model_config = {"populate_by_name": True}


class PlatformBootstrapCaching(BaseModel):
    cache_mode: str = Field(
        alias="cacheMode",
        description="Gateway caching mode for the descriptor.",
        examples=["request_scoped_composition"],
    )
    invalidation_owner: str = Field(
        alias="invalidationOwner",
        description=(
            "Owner responsible for invalidating stale capability truth. Shell bootstrap uses "
            "`upstream_service`; workspace descriptors use the dependency source key."
        ),
        examples=["upstream_service"],
    )
    stale_read_tolerance: str = Field(
        alias="staleReadTolerance",
        description="Governed stale-read tolerance classification.",
        examples=["bounded_navigation_refresh"],
    )
    revalidate_on_navigation: bool = Field(
        alias="revalidateOnNavigation",
        description="Whether the consumer should revalidate on navigation.",
        examples=[True],
    )
    ttl_seconds: int | None = Field(
        default=None,
        alias="ttlSeconds",
        description="Recommended time-to-live in seconds for the capability slice.",
        examples=[60],
    )
    correctness_critical: bool = Field(
        alias="correctnessCritical",
        description="Whether stale data would create a correctness risk for the consumer.",
        examples=[False],
    )

    model_config = {"populate_by_name": True}


class PlatformShellWorkspaceDescriptor(BaseModel):
    id: str = Field(description="Stable workspace identifier.", examples=["performance"])
    label: str = Field(description="Display label for the workspace.", examples=["Performance"])
    href: str = Field(
        description="Gateway navigation href for the workspace.", examples=["/performance"]
    )
    enabled: bool = Field(
        description="Whether the workspace should be enabled for the current platform posture.",
        examples=[True],
    )
    supportability: PlatformBootstrapSupportability = Field(
        description="Supportability posture for the workspace descriptor."
    )
    freshness: PlatformBootstrapFreshness = Field(
        description="Freshness metadata for the workspace descriptor."
    )
    evidence: PlatformBootstrapEvidence = Field(
        description="Evidence lineage and degraded-state metadata for the workspace descriptor."
    )
    versioning: PlatformBootstrapVersioning = Field(
        description="Version metadata for the workspace descriptor."
    )
    caching: PlatformBootstrapCaching = Field(
        description="Caching guidance for the workspace descriptor."
    )


class PlatformShellBootstrap(BaseModel):
    contract_version: str = Field(
        alias="contractVersion",
        description="Shell-bootstrap contract version emitted by gateway.",
        examples=["shell-bootstrap.v1"],
    )
    supportability: PlatformBootstrapSupportability = Field(
        description="Supportability posture for shell bootstrap."
    )
    freshness: PlatformBootstrapFreshness = Field(
        description="Freshness metadata for shell bootstrap."
    )
    evidence: PlatformBootstrapEvidence = Field(
        description="Evidence lineage and degraded-state metadata for shell bootstrap."
    )
    versioning: PlatformBootstrapVersioning = Field(
        description="Version metadata for shell bootstrap."
    )
    caching: PlatformBootstrapCaching = Field(description="Caching guidance for shell bootstrap.")
    workspaces: list[PlatformShellWorkspaceDescriptor] = Field(
        default_factory=list,
        description="Workspace descriptors emitted for shell navigation and gating.",
    )

    model_config = {"populate_by_name": True}
