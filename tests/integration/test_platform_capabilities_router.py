from fastapi.testclient import TestClient

from app.contracts.platform_capabilities import PlatformCapabilitiesResponse
from app.main import app

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


def test_platform_capabilities_router_success(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-core",
            "contractVersion": "v1",
            "policyVersion": "lotus-core-default-v1",
            "features": [
                {"key": "pas.integration.core_snapshot", "enabled": True},
                {"key": "pas.ingestion.bulk_upload", "enabled": True},
            ],
            "workflows": [{"workflow_key": "portfolio_bulk_onboarding", "enabled": True}],
            "supportedInputModes": ["pas_ref"],
        }

    async def _analytics(self, *args, **kwargs):
        if "risk" in self._base_url:
            return 200, {
                "sourceService": "lotus-risk",
                "contractVersion": "v1",
                "policyVersion": "lotus-risk-default-v1",
                "features": [{"key": "risk.analytics.risk_analytics", "enabled": True}],
                "workflows": [{"workflow_key": "risk_snapshot", "enabled": True}],
                "supportedInputModes": ["pas_ref"],
            }
        return 200, {
            "sourceService": "lotus-performance",
            "contractVersion": "v1",
            "policyVersion": "lotus-performance-default-v1",
            "features": [{"key": "performance.analytics.twr", "enabled": True}],
            "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-advise",
            "contractVersion": "v1",
            "policyVersion": "lotus-manage-default-v1",
            "features": [
                {"key": "dpm.proposals.lifecycle", "enabled": True},
                {"key": "dpm.support.run_apis", "enabled": True},
            ],
            "workflows": [{"workflow_key": "proposal_lifecycle", "enabled": True}],
            "supportedInputModes": ["portfolio_id", "inline_bundle"],
        }

    async def _ras(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-report",
            "contractVersion": "v1",
            "policyVersion": "lotus-report-default-v1",
            "features": [
                {"key": "ras.reporting.portfolio_summary", "enabled": True},
                {"key": "ras.reporting.portfolio_review", "enabled": True},
            ],
            "workflows": [{"workflow_key": "portfolio_reporting", "enabled": True}],
            "supportedInputModes": ["portfolio_id"],
        }

    async def _pas_policy(*args, **kwargs):
        return 200, {
            "policyProvenance": {
                "policyVersion": "lotus-core-default-v1",
                "policySource": "tenant",
                "matchedRuleId": "tenant.default.consumers.lotus-gateway",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW", "HOLDINGS"],
            "warnings": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_capabilities", _pas)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_effective_policy", _pas_policy)
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_capabilities", _analytics
    )
    monkeypatch.setattr("app.clients.advise_client.AdviseClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.reporting_client.ReportingClient.get_capabilities", _ras)

    client = TestClient(app)
    response = client.get(
        "/api/v1/platform/capabilities?consumerSystem=lotus-gateway&tenantId=default"
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["partialFailure"] is False
    assert set(body["sources"].keys()) == {
        "lotus_core",
        "lotus_performance",
        "lotus_risk",
        "lotus_advise",
        "lotus_manage",
        "lotus_report",
    }
    assert body["normalized"]["navigation"]["command_center"] is True
    assert body["normalized"]["navigation"]["decision_console"] is True
    assert body["normalized"]["navigation"]["reporting_hub"] is True
    assert body["normalized"]["navigation"]["portfolio_workspace"] is True
    assert body["normalized"]["navigation"]["performance_workspace"] is True
    assert body["normalized"]["navigation"]["risk_workspace"] is True
    assert body["normalized"]["navigation"]["proposal_workspace"] is True
    assert body["normalized"]["navigation"]["advisory_workspace"] is True
    assert body["normalized"]["workflowFlags"]["proposal_lifecycle"] is True
    assert body["normalized"]["workflowFlags"]["portfolio_reporting"] is True
    assert body["normalized"]["policyVersionsBySource"] == {
        "lotus_core": "lotus-core-default-v1",
        "lotus_performance": "lotus-performance-default-v1",
        "lotus_risk": "lotus-risk-default-v1",
        "lotus_advise": "lotus-manage-default-v1",
        "lotus_manage": "lotus-manage-default-v1",
        "lotus_report": "lotus-report-default-v1",
    }
    assert body["normalized"]["lotusCorePolicyDiagnostics"]["available"] is True
    shell_bootstrap = body["normalized"]["shellBootstrap"]
    assert shell_bootstrap["contractVersion"] == "shell-bootstrap.v1"
    assert shell_bootstrap["supportability"]["state"] == "ready"
    assert shell_bootstrap["evidence"]["lineageSources"] == [
        "lotus_core",
        "lotus_performance",
        "lotus_advise",
        "lotus_manage",
        "lotus_report",
        "lotus_risk",
    ]
    assert shell_bootstrap["versioning"]["sourcePolicyVersions"] == {
        "lotus_core": "lotus-core-default-v1",
        "lotus_performance": "lotus-performance-default-v1",
        "lotus_risk": "lotus-risk-default-v1",
        "lotus_advise": "lotus-manage-default-v1",
        "lotus_manage": "lotus-manage-default-v1",
        "lotus_report": "lotus-report-default-v1",
    }
    assert shell_bootstrap["caching"]["cacheMode"] == "request_scoped_composition"
    assert shell_bootstrap["caching"]["invalidationOwner"] == "upstream_service"
    assert [workspace["id"] for workspace in shell_bootstrap["workspaces"]] == [
        "portfolio",
        "performance",
        "risk",
        "proposal",
        "advisory",
    ]
    performance_workspace = next(
        workspace for workspace in shell_bootstrap["workspaces"] if workspace["id"] == "performance"
    )
    assert performance_workspace["enabled"] is True
    assert performance_workspace["freshness"]["freshnessClass"] == "analytical_summary"
    assert performance_workspace["caching"]["cacheMode"] == "short_lived_revalidation"
    risk_workspace = next(
        workspace for workspace in shell_bootstrap["workspaces"] if workspace["id"] == "risk"
    )
    assert risk_workspace["enabled"] is True
    assert risk_workspace["versioning"]["sourcePolicyVersion"] == "lotus-risk-default-v1"
    assert risk_workspace["evidence"]["lineageSources"] == ["lotus_risk"]
    proposal_workspace = next(
        workspace for workspace in shell_bootstrap["workspaces"] if workspace["id"] == "proposal"
    )
    assert proposal_workspace["enabled"] is True
    assert proposal_workspace["supportability"]["state"] == "ready"
    assert proposal_workspace["caching"]["correctnessCritical"] is True


def test_platform_capabilities_router_preserves_correlation_and_query_context(monkeypatch):
    captured: dict[str, str] = {}

    async def _service(self, consumer_system: str, tenant_id: str, correlation_id: str):
        captured["consumer_system"] = consumer_system
        captured["tenant_id"] = tenant_id
        captured["correlation_id"] = correlation_id
        return PlatformCapabilitiesResponse.model_validate(
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "tenantId": tenant_id,
                    "contractVersion": "v1",
                    "sources": {},
                    "partialFailure": False,
                    "errors": [],
                    "normalized": {
                        "navigation": {},
                        "workflowFlags": {},
                        "inputModesBySource": {},
                        "inputModesUnion": [],
                        "moduleHealth": {},
                        "policyVersionsBySource": {},
                        "lotusCorePolicyDiagnostics": {
                            "available": False,
                            "allowedSections": [],
                            "warnings": [],
                            "policyProvenance": {
                                "policyVersion": "unknown",
                                "policySource": "unknown",
                                "matchedRuleId": "unknown",
                                "strictMode": False,
                            },
                        },
                        "shellBootstrap": {
                            "contractVersion": "shell-bootstrap.v1",
                            "supportability": {"state": "ready", "reasons": []},
                            "freshness": {
                                "state": "current",
                                "freshnessClass": "shell_navigation",
                                "evaluatedAt": "2026-04-16T00:00:00Z",
                                "maxAgeSeconds": 60,
                            },
                            "evidence": {
                                "state": "source_backed",
                                "lineageSources": [],
                                "partialFailure": False,
                                "sourceErrorServices": [],
                            },
                            "versioning": {
                                "shellContractVersion": "shell-bootstrap.v1",
                                "capabilityContractVersion": "v1",
                                "sourcePolicyVersion": None,
                                "sourcePolicyVersions": {},
                            },
                            "caching": {
                                "cacheMode": "request_scoped_composition",
                                "invalidationOwner": "lotus_core",
                                "staleReadTolerance": "bounded_navigation_refresh",
                                "revalidateOnNavigation": True,
                                "ttlSeconds": 60,
                                "correctnessCritical": False,
                            },
                            "workspaces": [],
                        },
                    },
                }
            }
        )

    monkeypatch.setattr(
        "app.services.platform_capabilities_service.PlatformCapabilitiesService.get_platform_capabilities",
        _service,
    )

    client = TestClient(app)
    response = client.get(
        "/api/v1/platform/capabilities?consumerSystem=lotus-workbench&tenantId=tenant-a",
        headers={"X-Correlation-Id": "corr-platform-1"},
    )

    assert response.status_code == 200
    assert captured == {
        "consumer_system": "lotus-workbench",
        "tenant_id": "tenant-a",
        "correlation_id": "corr-platform-1",
    }
    body = response.json()["data"]
    assert body["consumerSystem"] == "lotus-workbench"
    assert body["tenantId"] == "tenant-a"


def test_platform_capabilities_router_partial_failure(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-core",
            "contractVersion": "v1",
            "policyVersion": "lotus-core-default-v1",
            "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
            "workflows": [],
            "supportedInputModes": ["pas_ref"],
        }

    async def _analytics(self, *args, **kwargs):
        if "risk" in self._base_url:
            return 504, {"detail": "risk unavailable"}
        return 500, {"detail": "upstream failed"}

    async def _dpm(*args, **kwargs):
        raise RuntimeError("upstream exception")

    async def _ras(*args, **kwargs):
        return 500, {"detail": "upstream failed"}

    async def _pas_policy(*args, **kwargs):
        return 503, {"detail": "policy unavailable"}

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_capabilities", _pas)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_effective_policy", _pas_policy)
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_capabilities", _analytics
    )
    monkeypatch.setattr("app.clients.advise_client.AdviseClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.reporting_client.ReportingClient.get_capabilities", _ras)

    client = TestClient(app)
    response = client.get(
        "/api/v1/platform/capabilities?consumerSystem=lotus-gateway&tenantId=default"
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["partialFailure"] is True
    assert set(body["sources"].keys()) == {"lotus_core"}
    assert len(body["errors"]) == 6
    assert body["normalized"]["navigation"]["analytics_studio"] is False
    assert body["normalized"]["navigation"]["portfolio_workspace"] is True
    assert body["normalized"]["navigation"]["performance_workspace"] is False
    assert body["normalized"]["navigation"]["risk_workspace"] is False
    assert body["normalized"]["moduleHealth"]["lotus_performance"] == "unavailable"
    assert body["normalized"]["moduleHealth"]["lotus_risk"] == "unavailable"
    assert body["normalized"]["moduleHealth"]["lotus_report"] == "unavailable"
    assert body["normalized"]["policyVersionsBySource"]["lotus_core"] == "lotus-core-default-v1"
    assert body["normalized"]["policyVersionsBySource"]["lotus_performance"] == "unknown"
    assert body["normalized"]["policyVersionsBySource"]["lotus_risk"] == "unknown"
    assert body["normalized"]["policyVersionsBySource"]["lotus_report"] == "unknown"
    assert body["normalized"]["lotusCorePolicyDiagnostics"]["available"] is False
    shell_bootstrap = body["normalized"]["shellBootstrap"]
    assert shell_bootstrap["supportability"]["state"] == "partial"
    assert shell_bootstrap["evidence"]["partialFailure"] is True
    assert shell_bootstrap["evidence"]["lineageSources"] == [
        "lotus_core",
        "lotus_performance",
        "lotus_advise",
        "lotus_manage",
        "lotus_report",
        "lotus_risk",
    ]
    assert "lotus_performance" in shell_bootstrap["evidence"]["sourceErrorServices"]
    performance_workspace = next(
        workspace for workspace in shell_bootstrap["workspaces"] if workspace["id"] == "performance"
    )
    assert performance_workspace["enabled"] is False
    assert performance_workspace["supportability"]["state"] == "partial"
    assert performance_workspace["evidence"]["state"] == "partial"
    risk_workspace = next(
        workspace for workspace in shell_bootstrap["workspaces"] if workspace["id"] == "risk"
    )
    assert risk_workspace["enabled"] is False
    assert risk_workspace["supportability"]["state"] == "partial"
    assert risk_workspace["evidence"]["sourceErrorServices"] == ["lotus_risk"]
