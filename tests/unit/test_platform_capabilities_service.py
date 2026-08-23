import asyncio
import time

import pytest

from app.services.platform_capabilities_feature_flags import (
    feature_enabled,
    feature_enablement,
    workflow_enabled,
)
from app.services.platform_capabilities_normalization import module_health, navigation_flags
from app.services.platform_capabilities_service import PlatformCapabilitiesService


class _StubClient:
    def __init__(
        self,
        status_code: int,
        payload: dict,
        policy_status_code: int = 200,
        policy_payload: dict | None = None,
        raise_policy_exception: bool = False,
    ):
        self.status_code = status_code
        self.payload = payload
        self.raise_policy_exception = raise_policy_exception
        self.policy_status_code = policy_status_code
        self.policy_payload = policy_payload or {
            "policyProvenance": {
                "policyVersion": "lotus-core-default-v1",
                "policySource": "default",
                "matchedRuleId": "default",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW"],
            "warnings": [],
        }

    async def get_capabilities(
        self,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ):
        return self.status_code, self.payload

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        if self.raise_policy_exception:
            raise RuntimeError("policy endpoint timeout")
        return self.policy_status_code, self.policy_payload


class _ErrorClient:
    async def get_capabilities(
        self,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ):
        raise RuntimeError("upstream unavailable")

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        raise RuntimeError("upstream unavailable")


class _RecordingStubClient(_StubClient):
    def __init__(self, status_code: int, payload: dict):
        super().__init__(status_code, payload)
        self.calls: list[dict[str, str | None]] = []

    async def get_capabilities(
        self,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ):
        self.calls.append(
            {
                "correlation_id": correlation_id,
                "consumer_system": consumer_system,
                "tenant_id": tenant_id,
            }
        )
        return await super().get_capabilities(
            correlation_id=correlation_id,
            consumer_system=consumer_system,
            tenant_id=tenant_id,
        )


def _feature_enabled(**overrides: bool) -> dict[str, bool]:
    flags = {
        "lotus_core_snapshot": True,
        "lotus_core_intake": False,
        "lotus_performance_analytics": False,
        "lotus_advise_lifecycle": False,
        "lotus_manage_support": False,
        "lotus_report_reporting": False,
        "lotus_risk_analytics": False,
    }
    flags.update(overrides)
    return flags


def test_navigation_flags_gate_command_center_on_manage_support() -> None:
    assert navigation_flags(_feature_enabled(lotus_manage_support=True))["command_center"] is True
    assert navigation_flags(_feature_enabled(lotus_manage_support=False))["command_center"] is False


def test_navigation_flags_keep_command_center_closed_when_manage_posture_absent() -> None:
    navigation = navigation_flags(_feature_enabled())

    assert navigation["command_center"] is False
    assert navigation["decision_console"] is False


def test_legacy_dpm_proposal_lifecycle_key_no_longer_enables_manage_or_advise() -> None:
    flags = feature_enablement(
        {
            "lotus_advise": {
                "features": [{"key": "dpm.proposals.lifecycle", "enabled": True}],
            },
            "lotus_manage": {
                "features": [{"key": "dpm.proposals.lifecycle", "enabled": True}],
            },
        }
    )

    assert flags["lotus_advise_lifecycle"] is False
    assert flags["lotus_manage_support"] is False


class _DelayedStubClient(_StubClient):
    def __init__(
        self,
        status_code: int,
        payload: dict,
        *,
        delay_seconds: float,
        policy_status_code: int = 200,
        policy_payload: dict | None = None,
        policy_delay_seconds: float | None = None,
    ):
        super().__init__(
            status_code,
            payload,
            policy_status_code=policy_status_code,
            policy_payload=policy_payload,
        )
        self.delay_seconds = delay_seconds
        self.policy_delay_seconds = (
            delay_seconds if policy_delay_seconds is None else policy_delay_seconds
        )

    async def get_capabilities(
        self,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ):
        await asyncio.sleep(self.delay_seconds)
        return await super().get_capabilities(
            correlation_id=correlation_id,
            consumer_system=consumer_system,
            tenant_id=tenant_id,
        )

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ):
        await asyncio.sleep(self.policy_delay_seconds)
        return await super().get_effective_policy(
            consumer_system=consumer_system,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )


class _NeverCompletingCapabilitiesClient(_StubClient):
    def __init__(self, status_code: int, payload: dict, *, blocker: asyncio.Event):
        super().__init__(status_code, payload)
        self.blocker = blocker

    async def get_capabilities(
        self,
        correlation_id: str,
        consumer_system: str | None = None,
        tenant_id: str | None = None,
    ):
        await self.blocker.wait()
        return await super().get_capabilities(
            correlation_id=correlation_id,
            consumer_system=consumer_system,
            tenant_id=tenant_id,
        )


@pytest.mark.asyncio
async def test_platform_capabilities_all_sources_success():
    service = PlatformCapabilitiesService(
        advise_client=_StubClient(
            200,
            {
                "sourceService": "lotus_advise",
                "policyVersion": "advise-tenant-a-v2",
                "supportedInputModes": ["pas_ref", "inline_bundle"],
                "features": [
                    {"key": "advisory.proposals.lifecycle", "enabled": True},
                ],
                "workflows": [{"workflow_key": "advisory_proposal_lifecycle", "enabled": True}],
                "supportability": {
                    "state": "ready",
                    "reason": "advisory_ready",
                    "freshness_bucket": "current",
                },
            },
        ),
        manage_client=_StubClient(
            200,
            {
                "sourceService": "lotus_manage",
                "policyVersion": "manage-tenant-a-v2",
                "supportedInputModes": ["portfolio_id"],
                "features": [{"key": "dpm.support.run_apis", "enabled": True}],
                "workflows": [],
            },
        ),
        lotus_core_query_client=_StubClient(
            200,
            {
                "sourceService": "lotus_core",
                "policyVersion": "pas-tenant-a-v3",
                "supportedInputModes": ["pas_ref"],
                "features": [
                    {"key": "pas.integration.core_snapshot", "enabled": True},
                    {"key": "pas.ingestion.bulk_upload", "enabled": True},
                ],
                "workflows": [{"workflow_key": "portfolio_bulk_onboarding", "enabled": True}],
            },
            policy_payload={
                "policyProvenance": {
                    "policyVersion": "pas-policy-v7",
                    "policySource": "tenant",
                    "matchedRuleId": "tenant.default.consumers.lotus-gateway",
                    "strictMode": True,
                },
                "allowedSections": ["OVERVIEW", "HOLDINGS"],
                "warnings": ["SECTIONS_FILTERED_BY_POLICY"],
            },
        ),
        analytics_client=_StubClient(
            200,
            {
                "sourceService": "lotus_performance",
                "policyVersion": "lotus-performance-tenant-a-v4",
                "supportedInputModes": ["pas_ref", "inline_bundle"],
                "features": [{"key": "performance.analytics.twr", "enabled": True}],
                "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            },
        ),
        reporting_client=_StubClient(
            200,
            {
                "sourceService": "lotus-report",
                "policyVersion": "ras-tenant-a-v1",
                "supportedInputModes": ["portfolio_id"],
                "features": [
                    {"key": "ras.reporting.portfolio_summary", "enabled": True},
                    {"key": "ras.reporting.portfolio_review", "enabled": True},
                ],
                "workflows": [{"workflow_key": "portfolio_reporting", "enabled": True}],
            },
        ),
        risk_client=_StubClient(
            200,
            {
                "sourceService": "lotus-risk",
                "policyVersion": "risk-tenant-a-v2",
                "supportedInputModes": ["pas_ref"],
                "features": [{"key": "risk.analytics.risk_analytics", "enabled": True}],
                "workflows": [{"workflow_key": "risk_snapshot", "enabled": True}],
            },
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-1",
    )

    assert response.data.partial_failure is False
    assert set(response.data.sources.keys()) == {
        "lotus_core",
        "lotus_performance",
        "lotus_risk",
        "lotus_advise",
        "lotus_manage",
        "lotus_report",
    }
    assert response.data.errors == []
    assert response.data.normalized.navigation["command_center"] is True
    assert response.data.normalized.navigation["portfolio_intake"] is True
    assert response.data.normalized.navigation["analytics_studio"] is True
    assert response.data.normalized.navigation["advisory_pipeline"] is True
    assert response.data.normalized.navigation["reporting_hub"] is True
    assert response.data.normalized.navigation["portfolio_workspace"] is True
    assert response.data.normalized.navigation["performance_workspace"] is True
    assert response.data.normalized.navigation["risk_workspace"] is True
    assert response.data.normalized.navigation["proposal_workspace"] is True
    assert response.data.normalized.navigation["advisory_workspace"] is True
    assert response.data.normalized.workflow_flags["proposal_lifecycle"] is True
    assert response.data.normalized.workflow_flags["portfolio_reporting"] is True
    assert "inline_bundle" in response.data.normalized.input_modes_union
    assert response.data.normalized.module_health["lotus_core"] == "available"
    assert response.data.normalized.policy_versions_by_source == {
        "lotus_core": "pas-tenant-a-v3",
        "lotus_performance": "lotus-performance-tenant-a-v4",
        "lotus_risk": "risk-tenant-a-v2",
        "lotus_advise": "advise-tenant-a-v2",
        "lotus_manage": "manage-tenant-a-v2",
        "lotus_report": "ras-tenant-a-v1",
    }
    assert response.data.normalized.lotus_core_policy_diagnostics["available"] is True
    assert response.data.normalized.lotus_core_policy_diagnostics["policyProvenance"] == {
        "policyVersion": "pas-policy-v7",
        "policySource": "tenant",
        "matchedRuleId": "tenant.default.consumers.lotus-gateway",
        "strictMode": True,
    }
    shell_bootstrap = response.data.normalized.shell_bootstrap
    assert shell_bootstrap.contract_version == "shell-bootstrap.v1"
    assert shell_bootstrap.supportability.state == "ready"
    assert shell_bootstrap.evidence.lineage_sources == [
        "lotus_core",
        "lotus_performance",
        "lotus_advise",
        "lotus_manage",
        "lotus_report",
        "lotus_risk",
    ]
    assert shell_bootstrap.versioning.capability_contract_version == "v1"
    assert shell_bootstrap.versioning.source_policy_versions == {
        "lotus_core": "pas-tenant-a-v3",
        "lotus_performance": "lotus-performance-tenant-a-v4",
        "lotus_risk": "risk-tenant-a-v2",
        "lotus_advise": "advise-tenant-a-v2",
        "lotus_manage": "manage-tenant-a-v2",
        "lotus_report": "ras-tenant-a-v1",
    }
    assert shell_bootstrap.caching.cache_mode == "request_scoped_composition"
    assert shell_bootstrap.caching.invalidation_owner == "upstream_service"
    performance_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "performance"
    )
    assert performance_workspace.enabled is True
    assert performance_workspace.freshness.freshness_class == "analytical_summary"
    assert performance_workspace.evidence.state == "source_backed"
    risk_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "risk"
    )
    assert risk_workspace.enabled is True
    assert risk_workspace.versioning.source_policy_version == "risk-tenant-a-v2"
    assert risk_workspace.evidence.lineage_sources == ["lotus_risk"]
    proposal_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "proposal"
    )
    assert proposal_workspace.enabled is True
    assert proposal_workspace.supportability.state == "ready"
    assert proposal_workspace.supportability.reasons == ["advisory_ready"]
    assert proposal_workspace.caching.correctness_critical is True


@pytest.mark.asyncio
async def test_platform_capabilities_partial_failure_on_error():
    service = PlatformCapabilitiesService(
        dpm_client=_ErrorClient(),
        lotus_core_query_client=_StubClient(
            200,
            {
                "sourceService": "lotus_core",
                "policyVersion": "pas-tenant-default-v1",
                "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
                "workflows": [],
            },
            policy_status_code=503,
            policy_payload={"detail": "service unavailable"},
        ),
        analytics_client=_StubClient(
            502,
            {
                "detail": {
                    "code": "PERFORMANCE_CAPABILITIES_UNAVAILABLE",
                    "message": "bad gateway",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        reporting_client=_StubClient(
            503,
            {
                "detail": "upstream failed",
                "client_name": "Private Client",
                "token": "secret-token",
            },
        ),
        risk_client=_StubClient(
            504,
            {
                "message": "risk timeout",
                "client_name": "Private Client",
                "token": "secret-token",
            },
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-2",
    )

    assert response.data.partial_failure is True
    assert set(response.data.sources.keys()) == {"lotus_core"}
    assert len(response.data.errors) == 6
    assert response.data.normalized.navigation["analytics_studio"] is False
    assert response.data.normalized.navigation["advisory_pipeline"] is False
    assert response.data.normalized.navigation["command_center"] is False
    assert response.data.normalized.navigation["portfolio_workspace"] is True
    assert response.data.normalized.navigation["performance_workspace"] is False
    assert response.data.normalized.navigation["risk_workspace"] is False
    assert response.data.normalized.navigation["proposal_workspace"] is False
    assert response.data.normalized.navigation["advisory_workspace"] is False
    assert response.data.normalized.module_health["lotus_performance"] == "unavailable"
    assert response.data.normalized.module_health["lotus_risk"] == "unavailable"
    assert response.data.normalized.module_health["lotus_advise"] == "unavailable"
    assert response.data.normalized.module_health["lotus_manage"] == "unavailable"
    assert response.data.normalized.module_health["lotus_report"] == "unavailable"
    assert any(
        error.detail == "PERFORMANCE_CAPABILITIES_UNAVAILABLE" for error in response.data.errors
    )
    assert any(error.detail == "capability source unavailable" for error in response.data.errors)
    assert "Private Client" not in str(response.data.errors)
    assert "secret-token" not in str(response.data.errors)
    assert response.data.normalized.policy_versions_by_source == {
        "lotus_core": "pas-tenant-default-v1",
        "lotus_performance": "unknown",
        "lotus_risk": "unknown",
        "lotus_advise": "unknown",
        "lotus_manage": "unknown",
        "lotus_report": "unknown",
    }
    assert response.data.normalized.lotus_core_policy_diagnostics["available"] is False
    assert (
        "LOTUS_CORE_POLICY_ENDPOINT_UNAVAILABLE"
        in (response.data.normalized.lotus_core_policy_diagnostics["warnings"])
    )
    shell_bootstrap = response.data.normalized.shell_bootstrap
    assert shell_bootstrap.supportability.state == "partial"
    assert "lotus_performance:502" in shell_bootstrap.supportability.reasons
    assert shell_bootstrap.evidence.partial_failure is True
    performance_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "performance"
    )
    assert performance_workspace.supportability.state == "partial"
    assert performance_workspace.evidence.state == "partial"
    assert performance_workspace.evidence.partial_failure is True
    risk_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "risk"
    )
    assert risk_workspace.enabled is False
    assert risk_workspace.supportability.state == "partial"
    assert risk_workspace.evidence.source_error_services == ["lotus_risk"]
    proposal_workspace = next(
        workspace for workspace in shell_bootstrap.workspaces if workspace.id == "proposal"
    )
    assert proposal_workspace.supportability.state == "partial"
    assert proposal_workspace.evidence.state == "partial"


@pytest.mark.asyncio
async def test_platform_capabilities_normalization_handles_malformed_feature_shapes():
    service = PlatformCapabilitiesService(
        dpm_client=_StubClient(
            200,
            {
                "sourceService": "lotus_manage",
                "policyVersion": "dpm-v1",
                "features": "invalid",
                "workflows": "invalid",
            },
        ),
        lotus_core_query_client=_StubClient(
            200,
            {
                "sourceService": "lotus_core",
                "policyVersion": "pas-v1",
                "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
                "workflows": [{"workflow_key": "portfolio_bulk_onboarding", "enabled": True}],
                "supportedInputModes": "pas_ref",
            },
            policy_payload={
                "policyProvenance": "invalid",
                "allowedSections": "invalid",
                "warnings": "invalid",
            },
        ),
        analytics_client=_StubClient(
            200,
            {
                "sourceService": "lotus_performance",
                "policyVersion": "lotus-performance-v1",
                "features": [{"key": "performance.analytics.twr", "enabled": False}],
                "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            },
        ),
        reporting_client=_StubClient(
            200,
            {
                "sourceService": "lotus-report",
                "policyVersion": "ras-v1",
                "features": [{"key": "ras.reporting.portfolio_summary", "enabled": True}],
                "workflows": [{"workflow_key": "portfolio_reporting", "enabled": False}],
            },
        ),
        risk_client=_StubClient(
            200,
            {
                "sourceService": "lotus-risk",
                "policyVersion": "risk-v1",
                "features": [{"key": "risk.analytics.risk_analytics", "enabled": True}],
                "workflows": [{"workflow_key": "risk_snapshot", "enabled": True}],
            },
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-3",
    )

    normalized = response.data.normalized
    assert normalized.navigation["command_center"] is False
    assert normalized.navigation["portfolio_intake"] is True
    assert normalized.navigation["advisory_pipeline"] is False
    assert normalized.navigation["analytics_studio"] is False
    assert normalized.navigation["portfolio_workspace"] is True
    assert normalized.navigation["performance_workspace"] is False
    assert normalized.navigation["risk_workspace"] is True
    assert normalized.workflow_flags["proposal_lifecycle"] is False
    assert normalized.workflow_flags["performance_snapshot"] is True
    assert normalized.input_modes_by_source["lotus_core"] == []
    assert normalized.lotus_core_policy_diagnostics["available"] is True
    assert normalized.lotus_core_policy_diagnostics["allowedSections"] == []
    assert normalized.lotus_core_policy_diagnostics["warnings"] == []
    assert (
        normalized.lotus_core_policy_diagnostics["policyProvenance"]["policyVersion"] == "unknown"
    )


@pytest.mark.asyncio
async def test_platform_capabilities_records_pas_policy_exception():
    service = PlatformCapabilitiesService(
        dpm_client=_StubClient(
            200,
            {"sourceService": "lotus_manage", "features": [], "workflows": []},
        ),
        lotus_core_query_client=_StubClient(
            200,
            {"sourceService": "lotus_core", "features": [], "workflows": []},
            raise_policy_exception=True,
        ),
        analytics_client=_StubClient(
            200,
            {"sourceService": "lotus_performance", "features": [], "workflows": []},
        ),
        reporting_client=_StubClient(
            200,
            {"sourceService": "lotus-report", "features": [], "workflows": []},
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-policy-ex",
    )
    error_services = {item.service for item in response.data.errors}
    assert "lotus_core_policy" in error_services


def test_platform_capabilities_feature_and_workflow_skip_non_dict_entries():
    sources = {
        "lotus_performance": {
            "features": ["bad", {"key": "performance.analytics.twr", "enabled": True}]
        },
        "lotus_advise": {
            "workflows": ["bad", {"workflow_key": "proposal_lifecycle", "enabled": True}]
        },
    }
    assert (
        feature_enabled(
            sources=sources,
            source_name="lotus_performance",
            feature_keys=("performance.analytics.twr",),
        )
        is True
    )
    assert (
        workflow_enabled(
            sources=sources, source_name="lotus_advise", workflow_key="proposal_lifecycle"
        )
        is True
    )


@pytest.mark.asyncio
async def test_platform_capabilities_preserves_advise_supportability_without_local_inference():
    service = PlatformCapabilitiesService(
        advise_client=_StubClient(
            200,
            {
                "source_service": "lotus-advise",
                "policy_version": "advisory.v1",
                "features": [
                    {
                        "key": "advisory.proposals.lifecycle",
                        "enabled": True,
                        "operational_ready": True,
                    },
                    {
                        "key": "advise.observability.advisory_supportability",
                        "enabled": True,
                        "operational_ready": True,
                    },
                ],
                "workflows": [
                    {"workflow_key": "advisory_proposal_lifecycle", "enabled": True},
                ],
                "supportability": {
                    "state": "degraded",
                    "reason": "dependency_degraded",
                    "freshness_bucket": "unknown",
                    "dependency_count": 5,
                    "ready_dependency_count": 4,
                    "degraded_dependency_count": 1,
                    "enabled_feature_count": 9,
                    "ready_feature_count": 8,
                },
            },
        ),
        manage_client=_StubClient(
            200,
            {"source_service": "lotus-manage", "features": [], "workflows": []},
        ),
        lotus_core_query_client=_StubClient(
            200,
            {
                "source_service": "lotus-core",
                "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
                "workflows": [],
            },
        ),
        analytics_client=_StubClient(
            200,
            {"source_service": "lotus-performance", "features": [], "workflows": []},
        ),
        reporting_client=_StubClient(
            200,
            {"source_service": "lotus-report", "features": [], "workflows": []},
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="default",
        correlation_id="corr-wtbd-004",
    )

    normalized = response.data.normalized
    assert normalized.navigation["advisory_pipeline"] is True
    assert normalized.workflow_flags["proposal_lifecycle"] is True
    assert response.data.sources["lotus_advise"]["supportability"]["state"] == "degraded"
    proposal_workspace = next(
        workspace
        for workspace in normalized.shell_bootstrap.workspaces
        if workspace.id == "proposal"
    )
    advisory_workspace = next(
        workspace
        for workspace in normalized.shell_bootstrap.workspaces
        if workspace.id == "advisory"
    )
    assert proposal_workspace.supportability.state == "degraded"
    assert proposal_workspace.supportability.reasons == ["dependency_degraded"]
    assert proposal_workspace.enabled is True
    assert advisory_workspace.supportability.state == "degraded"
    assert advisory_workspace.supportability.reasons == ["dependency_degraded"]
    assert advisory_workspace.enabled is True


def test_platform_capabilities_module_health_marks_unknown_sources():
    health = module_health(sources={"lotus_core": {}}, errors=[])
    assert health["lotus_core"] == "available"
    assert health["lotus_performance"] == "unknown"
    assert health["lotus_risk"] == "unknown"
    assert health["lotus_advise"] == "unknown"
    assert health["lotus_manage"] == "unknown"
    assert health["lotus_report"] == "unknown"


@pytest.mark.asyncio
async def test_platform_capabilities_uses_service_specific_upstream_capability_contracts():
    performance_client = _RecordingStubClient(
        200,
        {
            "sourceService": "lotus_performance",
            "policyVersion": "lotus-performance-v1",
            "features": [],
            "workflows": [],
        },
    )
    risk_client = _RecordingStubClient(
        200,
        {
            "sourceService": "lotus_risk",
            "policyVersion": "risk-v1",
            "features": [],
            "workflows": [],
        },
    )
    service = PlatformCapabilitiesService(
        dpm_client=_StubClient(
            200, {"sourceService": "lotus_manage", "features": [], "workflows": []}
        ),
        lotus_core_query_client=_StubClient(
            200, {"sourceService": "lotus_core", "features": [], "workflows": []}
        ),
        analytics_client=performance_client,
        reporting_client=_StubClient(
            200, {"sourceService": "lotus_report", "features": [], "workflows": []}
        ),
        risk_client=risk_client,
        contract_version="v1",
    )

    await service.get_platform_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-a",
        correlation_id="corr-shaped",
    )

    assert performance_client.calls == [
        {
            "correlation_id": "corr-shaped",
            "consumer_system": "lotus-workbench",
            "tenant_id": "tenant-a",
        }
    ]
    assert risk_client.calls == [
        {
            "correlation_id": "corr-shaped",
            "consumer_system": None,
            "tenant_id": None,
        }
    ]
    response = await service.get_platform_capabilities(
        consumer_system="lotus-workbench",
        tenant_id="tenant-a",
        correlation_id="corr-shaped-repeat",
    )
    assert response.data.sources["lotus_risk"]["sourceService"] == "lotus_risk"


@pytest.mark.asyncio
async def test_platform_capabilities_fetches_sources_concurrently():
    delay_seconds = 0.15
    service = PlatformCapabilitiesService(
        dpm_client=_DelayedStubClient(
            200,
            {"sourceService": "lotus_manage", "features": [], "workflows": []},
            delay_seconds=delay_seconds,
        ),
        lotus_core_query_client=_DelayedStubClient(
            200,
            {"sourceService": "lotus_core", "features": [], "workflows": []},
            delay_seconds=delay_seconds,
            policy_payload={
                "policyProvenance": {
                    "policyVersion": "pas-policy-v1",
                    "policySource": "tenant",
                    "matchedRuleId": "tenant.default.consumers.lotus-gateway",
                    "strictMode": False,
                },
                "allowedSections": ["OVERVIEW"],
                "warnings": [],
            },
        ),
        analytics_client=_DelayedStubClient(
            200,
            {"sourceService": "lotus_performance", "features": [], "workflows": []},
            delay_seconds=delay_seconds,
        ),
        reporting_client=_DelayedStubClient(
            200,
            {"sourceService": "lotus_report", "features": [], "workflows": []},
            delay_seconds=delay_seconds,
        ),
        contract_version="v1",
    )

    started_at = time.perf_counter()
    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-concurrency",
    )
    elapsed_seconds = time.perf_counter() - started_at

    assert response.data.partial_failure is False
    assert elapsed_seconds < 0.45


@pytest.mark.asyncio
async def test_platform_capabilities_timeout_budget_preserves_partial_response():
    for attempt in range(10):
        blocker = asyncio.Event()
        service = PlatformCapabilitiesService(
            dpm_client=_StubClient(
                200,
                {
                    "sourceService": "lotus_manage",
                    "features": [{"key": "dpm.support.run_apis", "enabled": True}],
                    "workflows": [],
                },
            ),
            lotus_core_query_client=_StubClient(
                200,
                {
                    "sourceService": "lotus_core",
                    "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
                    "workflows": [],
                },
            ),
            analytics_client=_NeverCompletingCapabilitiesClient(
                200,
                {
                    "sourceService": "lotus_performance",
                    "features": [{"key": "performance.analytics.twr", "enabled": True}],
                    "workflows": [],
                },
                blocker=blocker,
            ),
            reporting_client=_StubClient(
                200,
                {
                    "sourceService": "lotus_report",
                    "features": [{"key": "ras.reporting.portfolio_summary", "enabled": True}],
                    "workflows": [],
                },
            ),
            contract_version="v1",
            source_timeout_seconds=0.05,
        )

        started_at = time.perf_counter()
        response = await service.get_platform_capabilities(
            consumer_system="lotus-gateway",
            tenant_id="default",
            correlation_id=f"corr-timeout-budget-{attempt}",
        )
        elapsed_seconds = time.perf_counter() - started_at

        assert elapsed_seconds < 0.2
        assert response.data.partial_failure is True
        assert response.data.normalized.navigation["portfolio_workspace"] is True
        assert response.data.normalized.navigation["performance_workspace"] is False
        assert response.data.normalized.module_health["lotus_performance"] == "unavailable"
        assert {error.service for error in response.data.errors} == {"lotus_performance"}
        assert response.data.errors[0].detail == "upstream_exception:TimeoutError"


@pytest.mark.asyncio
async def test_platform_capabilities_keeps_advise_and_manage_capabilities_separate():
    advise_client = _RecordingStubClient(
        200,
        {
            "sourceService": "lotus_advise",
            "policyVersion": "advise-v2",
            "features": [{"key": "advise.proposals.lifecycle", "enabled": True}],
            "workflows": [
                {"workflow_key": "proposal_approval_flow", "enabled": True},
                {"workflow_key": "proposal_lifecycle", "enabled": True},
            ],
        },
    )
    manage_client = _RecordingStubClient(
        200,
        {
            "sourceService": "lotus_manage_split",
            "policyVersion": "manage-split-v2",
            "supportedInputModes": ["inline_bundle", "portfolio_id"],
            "features": [
                {"key": "dpm.support.run_apis", "enabled": True},
            ],
            "workflows": [],
        },
    )
    service = PlatformCapabilitiesService(
        advise_client=advise_client,
        lotus_core_query_client=_StubClient(
            200,
            {"sourceService": "lotus_core", "features": [], "workflows": []},
        ),
        analytics_client=_StubClient(
            200,
            {"sourceService": "lotus_performance", "features": [], "workflows": []},
        ),
        reporting_client=_StubClient(
            200,
            {"sourceService": "lotus_report", "features": [], "workflows": []},
        ),
        manage_client=manage_client,
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-manage-merge",
    )

    lotus_manage = response.data.sources["lotus_manage"]
    lotus_advise = response.data.sources["lotus_advise"]
    assert response.data.partial_failure is False
    assert response.data.errors == []
    assert advise_client.calls == [
        {
            "correlation_id": "corr-manage-merge",
            "consumer_system": "lotus-gateway",
            "tenant_id": "default",
        }
    ]
    assert manage_client.calls == [
        {
            "correlation_id": "corr-manage-merge",
            "consumer_system": "lotus-gateway",
            "tenant_id": "default",
        }
    ]
    assert lotus_advise["policyVersion"] == "advise-v2"
    assert lotus_manage["policyVersion"] == "manage-split-v2"
    assert lotus_manage["supportedInputModes"] == ["inline_bundle", "portfolio_id"]
    assert lotus_manage["features"] == [{"key": "dpm.support.run_apis", "enabled": True}]
    assert lotus_manage["workflows"] == []
    assert response.data.normalized.workflow_flags["proposal_lifecycle"] is True
    assert response.data.normalized.workflow_flags["proposal_approval_flow"] is True


@pytest.mark.asyncio
async def test_platform_capabilities_normalizes_live_snake_case_capability_metadata():
    service = PlatformCapabilitiesService(
        advise_client=_StubClient(
            200,
            {
                "source_service": "lotus-advise",
                "policy_version": "advise.policy.v1",
                "supported_input_modes": ["portfolio_id", "inline_bundle"],
                "features": [],
                "workflows": [],
            },
        ),
        manage_client=_StubClient(
            200,
            {
                "source_service": "lotus-manage",
                "policy_version": "manage.policy.v1",
                "supported_input_modes": ["portfolio_id"],
                "features": [],
                "workflows": [],
            },
        ),
        lotus_core_query_client=_StubClient(
            200,
            {
                "source_service": "lotus-core",
                "policy_version": "tenant-default-v1",
                "supported_input_modes": ["lotus_core_ref"],
                "features": [
                    {"key": "lotus_core.support.overview_api", "enabled": True},
                    {"key": "lotus_core.ingestion.bulk_upload_adapter", "enabled": True},
                    {"key": "lotus_core.ingestion.portfolio_bundle_adapter", "enabled": True},
                ],
                "workflows": [],
            },
        ),
        analytics_client=_StubClient(
            200,
            {
                "source_service": "lotus-performance",
                "policy_version": "tenant-default-v1",
                "supported_input_modes": ["stateful", "stateless"],
                "features": [],
                "workflows": [],
            },
        ),
        reporting_client=_StubClient(
            200,
            {
                "source_service": "lotus-report",
                "policy_version": "ras-default-v1",
                "supported_input_modes": ["portfolio_id"],
                "features": [],
                "workflows": [],
            },
        ),
        risk_client=_StubClient(
            200,
            {
                "source_service": "lotus-risk",
                "policy_version": "risk.v1",
                "supported_input_modes": ["stateless", "stateful", "simulation"],
                "features": [],
                "workflows": [],
            },
        ),
        contract_version="v1",
    )

    response = await service.get_platform_capabilities(
        consumer_system="lotus-gateway",
        tenant_id="default",
        correlation_id="corr-live-shape",
    )

    normalized = response.data.normalized
    assert normalized.input_modes_by_source == {
        "lotus_core": ["lotus_core_ref"],
        "lotus_performance": ["stateful", "stateless"],
        "lotus_advise": ["portfolio_id", "inline_bundle"],
        "lotus_manage": ["portfolio_id"],
        "lotus_report": ["portfolio_id"],
        "lotus_risk": ["stateless", "stateful", "simulation"],
    }
    assert normalized.input_modes_union == [
        "lotus_core_ref",
        "stateful",
        "stateless",
        "portfolio_id",
        "inline_bundle",
        "simulation",
    ]
    assert normalized.navigation["portfolio_intake"] is True
    assert normalized.navigation["portfolio_workspace"] is True
    assert normalized.policy_versions_by_source == {
        "lotus_core": "tenant-default-v1",
        "lotus_performance": "tenant-default-v1",
        "lotus_advise": "advise.policy.v1",
        "lotus_manage": "manage.policy.v1",
        "lotus_report": "ras-default-v1",
        "lotus_risk": "risk.v1",
    }
