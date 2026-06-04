from app.contracts.platform_capabilities import CapabilitySourceError
from app.services.platform_capabilities_shell import (
    build_shell_bootstrap,
    build_workspace_descriptor,
)


def test_build_shell_bootstrap_marks_partial_failure_and_workspace_errors() -> None:
    bootstrap = build_shell_bootstrap(
        sources={},
        navigation={
            "portfolio_workspace": False,
            "performance_workspace": False,
            "risk_workspace": False,
            "proposal_workspace": False,
            "advisory_workspace": False,
        },
        module_health_by_source={
            "lotus_core": "unknown",
            "lotus_performance": "unavailable",
            "lotus_risk": "unknown",
            "lotus_advise": "unknown",
        },
        policy_versions_by_source={
            "lotus_core": "unknown",
            "lotus_performance": "unknown",
            "lotus_advise": "unknown",
            "lotus_manage": "unknown",
            "lotus_report": "unknown",
            "lotus_risk": "unknown",
        },
        errors=[
            CapabilitySourceError(
                service="lotus_performance",
                status_code=503,
                detail="service unavailable",
            )
        ],
        evaluated_at="2026-06-04T00:00:00Z",
        contract_version="platform-capabilities.v1",
    )

    assert bootstrap.contract_version == "shell-bootstrap.v1"
    assert bootstrap.supportability.state == "partial"
    assert bootstrap.supportability.reasons == ["lotus_performance:503"]
    assert bootstrap.evidence.partial_failure is True
    assert bootstrap.evidence.source_error_services == ["lotus_performance"]
    assert bootstrap.versioning.capability_contract_version == "platform-capabilities.v1"

    performance_workspace = next(
        workspace for workspace in bootstrap.workspaces if workspace.id == "performance"
    )
    assert performance_workspace.supportability.state == "partial"
    assert performance_workspace.supportability.reasons == ["lotus_performance_unavailable"]
    assert performance_workspace.freshness.state == "partial"
    assert performance_workspace.evidence.partial_failure is True


def test_build_workspace_descriptor_uses_source_supportability_when_available() -> None:
    descriptor = build_workspace_descriptor(
        workspace_id="proposal",
        label="Proposal",
        href="/proposals",
        enabled=True,
        dependency_source="lotus_advise",
        source_supportability={"state": "degraded", "reason": "policy_review_required"},
        module_health_by_source={"lotus_advise": "available"},
        policy_versions_by_source={"lotus_advise": "advise.policy.v1"},
        error_services=[],
        evaluated_at="2026-06-04T00:00:00Z",
        contract_version="platform-capabilities.v1",
        freshness_class="workflow_truth",
        max_age_seconds=0,
        cache_mode="authoritative_read",
        stale_read_tolerance="none",
    )

    assert descriptor.enabled is True
    assert descriptor.supportability.state == "degraded"
    assert descriptor.supportability.reasons == ["policy_review_required"]
    assert descriptor.evidence.state == "source_backed"
    assert descriptor.versioning.source_policy_version == "advise.policy.v1"
    assert descriptor.caching.correctness_critical is True


def test_build_workspace_descriptor_marks_disabled_unknown_source() -> None:
    descriptor = build_workspace_descriptor(
        workspace_id="risk",
        label="Risk",
        href="/performance?mode=risk",
        enabled=False,
        dependency_source="lotus_risk",
        source_supportability=None,
        module_health_by_source={"lotus_risk": "unknown"},
        policy_versions_by_source={"lotus_risk": "unknown"},
        error_services=[],
        evaluated_at="2026-06-04T00:00:00Z",
        contract_version="platform-capabilities.v1",
        freshness_class="analytical_summary",
        max_age_seconds=120,
        cache_mode="short_lived_revalidation",
        stale_read_tolerance="bounded_analytical_read",
    )

    assert descriptor.enabled is False
    assert descriptor.supportability.state == "unavailable"
    assert descriptor.supportability.reasons == ["risk_disabled"]
    assert descriptor.evidence.state == "unavailable"
    assert descriptor.freshness.state == "unavailable"
    assert descriptor.evidence.partial_failure is False
