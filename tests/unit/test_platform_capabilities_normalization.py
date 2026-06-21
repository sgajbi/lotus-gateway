from typing import Any

from app.contracts.platform_capabilities import CapabilitySourceError
from app.services.platform_capabilities_feature_flags import (
    feature_enabled,
    workflow_enabled,
)
from app.services.platform_capabilities_normalization import (
    build_normalized_capabilities,
    module_health,
)


def test_build_normalized_capabilities_emits_source_backed_shell_bootstrap() -> None:
    normalized = build_normalized_capabilities(
        sources={
            "lotus_core": {
                "policyVersion": "core.policy.v1",
                "supportedInputModes": ["pas_ref"],
                "features": [
                    {"key": "lotus_core.support.overview_api", "enabled": True},
                    {"key": "lotus_core.ingestion.bulk_upload_adapter", "enabled": True},
                ],
                "workflows": [
                    {"workflow_key": "portfolio_bulk_onboarding", "enabled": True},
                ],
            },
            "lotus_performance": {
                "policyVersion": "performance.policy.v1",
                "supportedInputModes": ["stateful"],
                "features": [{"key": "lotus_performance.analytics.twr", "enabled": True}],
                "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            },
            "lotus_advise": {
                "policyVersion": "advise.policy.v1",
                "supportedInputModes": ["portfolio_id"],
                "features": [{"key": "advisory.proposals.lifecycle", "enabled": True}],
                "workflows": [{"workflow_key": "proposal_lifecycle", "enabled": True}],
                "supportability": {"state": "ready", "reason": "advisory_ready"},
            },
            "lotus_manage": {
                "policyVersion": "manage.policy.v1",
                "supportedInputModes": ["portfolio_id"],
                "features": [{"key": "dpm.support.run_apis", "enabled": True}],
                "workflows": [],
            },
            "lotus_report": {
                "policyVersion": "report.policy.v1",
                "supportedInputModes": ["portfolio_id"],
                "features": [
                    {"key": "lotus_report.reporting.portfolio_summary", "enabled": True},
                ],
                "workflows": [{"workflow_key": "portfolio_reporting", "enabled": True}],
            },
            "lotus_risk": {
                "policyVersion": "risk.policy.v1",
                "supportedInputModes": ["simulation"],
                "features": [{"key": "risk.analytics.metrics", "enabled": True}],
                "workflows": [],
            },
        },
        errors=[],
        lotus_core_policy={
            "policyProvenance": {
                "policyVersion": "core.policy.v1",
                "policySource": "tenant",
                "matchedRuleId": "tenant.default",
                "strictMode": True,
            },
            "allowedSections": ["OVERVIEW", "HOLDINGS"],
            "warnings": ["TENANT_POLICY_WARNING"],
        },
        evaluated_at="2026-06-04T00:00:00Z",
        contract_version="platform-capabilities.v1",
    )

    assert normalized.navigation["portfolio_workspace"] is True
    assert normalized.navigation["performance_workspace"] is True
    assert normalized.navigation["risk_workspace"] is True
    assert normalized.workflow_flags["portfolio_bulk_onboarding"] is True
    assert normalized.workflow_flags["proposal_lifecycle"] is True
    assert normalized.input_modes_union == ["pas_ref", "stateful", "portfolio_id", "simulation"]
    assert normalized.lotus_core_policy_diagnostics == {
        "available": True,
        "allowedSections": ["OVERVIEW", "HOLDINGS"],
        "warnings": ["TENANT_POLICY_WARNING"],
        "policyProvenance": {
            "policyVersion": "core.policy.v1",
            "policySource": "tenant",
            "matchedRuleId": "tenant.default",
            "strictMode": True,
        },
    }

    shell_bootstrap = normalized.shell_bootstrap
    assert shell_bootstrap.contract_version == "shell-bootstrap.v1"
    assert shell_bootstrap.supportability.state == "ready"
    assert shell_bootstrap.evidence.state == "source_backed"
    assert shell_bootstrap.evidence.partial_failure is False
    assert shell_bootstrap.versioning.capability_contract_version == "platform-capabilities.v1"

    proposal_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "proposal"
    )
    assert proposal_workspace.enabled is True
    assert proposal_workspace.supportability.state == "ready"
    assert proposal_workspace.supportability.reasons == ["advisory_ready"]
    assert proposal_workspace.caching.correctness_critical is True


def test_build_normalized_capabilities_marks_degraded_policy_and_missing_sources() -> None:
    normalized = build_normalized_capabilities(
        sources={
            "lotus_core": {
                "policy_version": "core.policy.v2",
                "supported_input_modes": ["pas_ref"],
                "features": [{"key": "lotus_core.support.overview_api", "enabled": True}],
                "workflows": [],
            },
        },
        errors=[
            CapabilitySourceError(
                service="lotus_performance",
                status_code=503,
                detail="service unavailable",
            ),
            CapabilitySourceError(
                service="lotus_core_policy",
                status_code=504,
                detail="policy timeout",
            ),
        ],
        lotus_core_policy=None,
        evaluated_at="2026-06-04T00:00:00Z",
        contract_version="platform-capabilities.v1",
    )

    assert normalized.module_health["lotus_core"] == "available"
    assert normalized.module_health["lotus_performance"] == "unavailable"
    assert normalized.module_health["lotus_advise"] == "unknown"
    assert normalized.policy_versions_by_source["lotus_risk"] == "unknown"
    assert normalized.lotus_core_policy_diagnostics["warnings"] == [
        "LOTUS_CORE_POLICY_ENDPOINT_UNAVAILABLE"
    ]

    shell_bootstrap = normalized.shell_bootstrap
    assert shell_bootstrap.supportability.state == "partial"
    assert shell_bootstrap.supportability.reasons == [
        "lotus_performance:503",
        "lotus_core_policy:504",
    ]
    assert shell_bootstrap.evidence.partial_failure is True
    assert shell_bootstrap.evidence.source_error_services == [
        "lotus_performance",
        "lotus_core_policy",
    ]

    performance_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "performance"
    )
    assert performance_workspace.enabled is False
    assert performance_workspace.supportability.state == "partial"
    assert performance_workspace.supportability.reasons == ["lotus_performance_unavailable"]
    assert performance_workspace.evidence.partial_failure is True


def test_normalization_helpers_ignore_malformed_upstream_shapes() -> None:
    sources: dict[str, dict[str, Any]] = {
        "lotus_core": {
            "features": "not-a-feature-list",
            "workflows": {"workflow_key": "portfolio_bulk_onboarding", "enabled": True},
        },
        "lotus_advise": {
            "features": [
                "malformed",
                {"key": "advisory.proposals.lifecycle", "enabled": True},
            ],
            "workflows": [
                None,
                {"workflow_key": "proposal_lifecycle", "enabled": True},
            ],
        },
    }

    assert (
        feature_enabled(
            sources=sources,
            source_name="lotus_core",
            feature_keys=("lotus_core.support.overview_api",),
        )
        is False
    )
    assert (
        workflow_enabled(
            sources=sources,
            source_name="lotus_core",
            workflow_key="portfolio_bulk_onboarding",
        )
        is False
    )
    assert (
        feature_enabled(
            sources=sources,
            source_name="lotus_advise",
            feature_keys=("advisory.proposals.lifecycle",),
        )
        is True
    )
    assert (
        workflow_enabled(
            sources=sources,
            source_name="lotus_advise",
            workflow_key="proposal_lifecycle",
        )
        is True
    )


def test_module_health_classifies_available_unavailable_and_unknown_sources() -> None:
    health = module_health(
        sources={"lotus_core": {}, "lotus_advise": {}},
        errors=[
            CapabilitySourceError(
                service="lotus_report",
                status_code=500,
                detail="upstream exception",
            )
        ],
    )

    assert health == {
        "lotus_core": "available",
        "lotus_performance": "unknown",
        "lotus_advise": "available",
        "lotus_manage": "unknown",
        "lotus_report": "unavailable",
        "lotus_risk": "unknown",
    }
