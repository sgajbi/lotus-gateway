from fastapi.testclient import TestClient

from app.main import app

LOTUS_CORE_QUERY_CLIENT = "app.clients.lotus_core_query_client.LotusCoreQueryClient"


def test_platform_capabilities_contract_shape(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "lotus-core",
            "policyVersion": "lotus-core-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "performance-analytics",
            "policyVersion": "lotus-performance-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "lotus-advise",
            "policyVersion": "lotus-manage-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _ras(*args, **kwargs):
        return 200, {
            "contractVersion": "v1",
            "sourceService": "lotus-report",
            "policyVersion": "lotus-report-default-v1",
            "features": [],
            "workflows": [],
        }

    async def _pas_policy(*args, **kwargs):
        return 200, {
            "policyProvenance": {
                "policyVersion": "lotus-core-default-v1",
                "policySource": "default",
                "matchedRuleId": "default",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW"],
            "warnings": [],
        }

    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_capabilities", _pas)
    monkeypatch.setattr(f"{LOTUS_CORE_QUERY_CLIENT}.get_effective_policy", _pas_policy)
    monkeypatch.setattr(
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_capabilities", _pa
    )
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.reporting_client.ReportingClient.get_capabilities", _ras)

    client = TestClient(app)
    response = client.get(
        "/api/v1/platform/capabilities?consumerSystem=lotus-gateway&tenantId=default"
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["contractVersion"] == "v1"
    assert payload["consumerSystem"] == "lotus-gateway"
    assert payload["tenantId"] == "default"
    assert payload["partialFailure"] is False
    assert "normalized" in payload
    assert "navigation" in payload["normalized"]
    assert "workflowFlags" in payload["normalized"]
    assert "moduleHealth" in payload["normalized"]
    assert "policyVersionsBySource" in payload["normalized"]
    assert "lotusCorePolicyDiagnostics" in payload["normalized"]
    assert "shellBootstrap" in payload["normalized"]
    assert payload["normalized"]["navigation"]["portfolio_workspace"] is False
    assert payload["normalized"]["navigation"]["performance_workspace"] is False
    assert payload["normalized"]["navigation"]["risk_workspace"] is False
    assert payload["normalized"]["navigation"]["proposal_workspace"] is False
    assert payload["normalized"]["navigation"]["advisory_workspace"] is False
    assert payload["normalized"]["shellBootstrap"]["contractVersion"] == "shell-bootstrap.v1"
    assert payload["normalized"]["shellBootstrap"]["supportability"]["state"] == "ready"
    assert (
        payload["normalized"]["shellBootstrap"]["freshness"]["freshnessClass"] == "shell_navigation"
    )
    assert payload["normalized"]["shellBootstrap"]["evidence"]["state"] == "source_backed"
    assert (
        payload["normalized"]["shellBootstrap"]["versioning"]["capabilityContractVersion"] == "v1"
    )
    assert (
        payload["normalized"]["shellBootstrap"]["caching"]["cacheMode"]
        == "request_scoped_composition"
    )
    assert len(payload["normalized"]["shellBootstrap"]["workspaces"]) == 5

    for service_name in ("lotus_core", "lotus_performance", "lotus_manage", "lotus_report"):
        source = payload["sources"][service_name]
        assert source["contractVersion"] == "v1"
        assert "sourceService" in source


def test_platform_capabilities_openapi_contract_registered() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()

    operation = spec["paths"]["/api/v1/platform/capabilities"]["get"]
    assert operation["summary"] == "Get Aggregated Platform Capabilities"
    assert "concurrently" in operation["description"]
    assert "partial-failure diagnostics" in operation["description"]

    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert (
        "actual downstream product identity"
        in parameters["consumerSystem"]["schema"]["description"]
    )
    assert parameters["consumerSystem"]["schema"]["examples"] == [
        "lotus-gateway",
        "lotus-workbench",
    ]
    assert "default tenant" in parameters["tenantId"]["schema"]["description"]
    assert parameters["tenantId"]["schema"]["examples"] == ["default", "tenant-a"]
    assert parameters["X-Correlation-Id"]["description"]

    response_schema = spec["components"]["schemas"]["PlatformCapabilitiesResponse"]
    data_schema = spec["components"]["schemas"]["PlatformCapabilitiesData"]
    error_schema = spec["components"]["schemas"]["CapabilitySourceError"]
    normalized_schema = spec["components"]["schemas"]["PlatformCapabilitiesNormalized"]
    shell_bootstrap_schema = spec["components"]["schemas"]["PlatformShellBootstrap"]
    workspace_schema = spec["components"]["schemas"]["PlatformShellWorkspaceDescriptor"]
    supportability_schema = spec["components"]["schemas"]["PlatformBootstrapSupportability"]
    freshness_schema = spec["components"]["schemas"]["PlatformBootstrapFreshness"]
    evidence_schema = spec["components"]["schemas"]["PlatformBootstrapEvidence"]
    versioning_schema = spec["components"]["schemas"]["PlatformBootstrapVersioning"]
    caching_schema = spec["components"]["schemas"]["PlatformBootstrapCaching"]

    assert response_schema["properties"]["data"]["description"]
    assert data_schema["properties"]["consumerSystem"]["description"]
    assert data_schema["properties"]["tenantId"]["description"]
    assert data_schema["properties"]["contractVersion"]["description"]
    assert data_schema["properties"]["sources"]["description"]
    assert data_schema["properties"]["partialFailure"]["description"]
    assert data_schema["properties"]["errors"]["description"]
    assert data_schema["properties"]["normalized"]["description"]
    assert error_schema["properties"]["service"]["description"]
    assert error_schema["properties"]["status_code"]["description"]
    assert error_schema["properties"]["detail"]["description"]
    assert normalized_schema["properties"]["navigation"]["description"]
    assert normalized_schema["properties"]["workflowFlags"]["description"]
    assert normalized_schema["properties"]["inputModesBySource"]["description"]
    assert normalized_schema["properties"]["inputModesUnion"]["description"]
    assert normalized_schema["properties"]["moduleHealth"]["description"]
    assert normalized_schema["properties"]["policyVersionsBySource"]["description"]
    assert normalized_schema["properties"]["lotusCorePolicyDiagnostics"]["description"]
    assert normalized_schema["properties"]["shellBootstrap"]["description"]
    assert shell_bootstrap_schema["properties"]["contractVersion"]["description"]
    assert shell_bootstrap_schema["properties"]["supportability"]["description"]
    assert shell_bootstrap_schema["properties"]["freshness"]["description"]
    assert shell_bootstrap_schema["properties"]["evidence"]["description"]
    assert shell_bootstrap_schema["properties"]["versioning"]["description"]
    assert shell_bootstrap_schema["properties"]["caching"]["description"]
    assert shell_bootstrap_schema["properties"]["workspaces"]["description"]
    assert workspace_schema["properties"]["id"]["description"]
    assert workspace_schema["properties"]["label"]["description"]
    assert workspace_schema["properties"]["href"]["description"]
    assert workspace_schema["properties"]["enabled"]["description"]
    assert workspace_schema["properties"]["supportability"]["description"]
    assert workspace_schema["properties"]["freshness"]["description"]
    assert workspace_schema["properties"]["evidence"]["description"]
    assert workspace_schema["properties"]["versioning"]["description"]
    assert workspace_schema["properties"]["caching"]["description"]
    assert supportability_schema["properties"]["state"]["description"]
    assert supportability_schema["properties"]["reasons"]["description"]
    assert freshness_schema["properties"]["state"]["description"]
    assert freshness_schema["properties"]["freshnessClass"]["description"]
    assert freshness_schema["properties"]["evaluatedAt"]["description"]
    assert freshness_schema["properties"]["maxAgeSeconds"]["description"]
    assert evidence_schema["properties"]["state"]["description"]
    assert evidence_schema["properties"]["lineageSources"]["description"]
    assert evidence_schema["properties"]["partialFailure"]["description"]
    assert evidence_schema["properties"]["sourceErrorServices"]["description"]
    assert versioning_schema["properties"]["shellContractVersion"]["description"]
    assert versioning_schema["properties"]["capabilityContractVersion"]["description"]
    assert versioning_schema["properties"]["sourcePolicyVersion"]["description"]
    assert versioning_schema["properties"]["sourcePolicyVersions"]["description"]
    assert caching_schema["properties"]["cacheMode"]["description"]
    assert caching_schema["properties"]["invalidationOwner"]["description"]
    assert caching_schema["properties"]["staleReadTolerance"]["description"]
    assert caching_schema["properties"]["revalidateOnNavigation"]["description"]
    assert caching_schema["properties"]["ttlSeconds"]["description"]
    assert caching_schema["properties"]["correctnessCritical"]["description"]
