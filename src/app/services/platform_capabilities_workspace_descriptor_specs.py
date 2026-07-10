from dataclasses import dataclass

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
