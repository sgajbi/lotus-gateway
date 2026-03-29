from fastapi.testclient import TestClient

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

    async def _pa(*args, **kwargs):
        return 200, {
            "sourceService": "performance-analytics",
            "contractVersion": "v1",
            "policyVersion": "lotus-performance-default-v1",
            "features": [{"key": "pa.analytics.twr", "enabled": True}],
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
            "supportedInputModes": ["pas_ref", "inline_bundle"],
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
            "supportedInputModes": ["pas_ref"],
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
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_capabilities", _pa
    )
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
        "lotus_manage",
        "lotus_report",
    }
    assert body["normalized"]["navigation"]["decision_console"] is True
    assert body["normalized"]["navigation"]["reporting_hub"] is True
    assert body["normalized"]["workflowFlags"]["proposal_lifecycle"] is True
    assert body["normalized"]["workflowFlags"]["portfolio_reporting"] is True
    assert body["normalized"]["policyVersionsBySource"] == {
        "lotus_core": "lotus-core-default-v1",
        "lotus_performance": "lotus-performance-default-v1",
        "lotus_manage": "lotus-manage-default-v1",
        "lotus_report": "lotus-report-default-v1",
    }
    assert body["normalized"]["lotusCorePolicyDiagnostics"]["available"] is True


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

    async def _pa(*args, **kwargs):
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
        "app.clients.lotus_analytics_client.LotusAnalyticsClient.get_capabilities", _pa
    )
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
    assert len(body["errors"]) == 4
    assert body["normalized"]["navigation"]["analytics_studio"] is False
    assert body["normalized"]["moduleHealth"]["lotus_performance"] == "unavailable"
    assert body["normalized"]["moduleHealth"]["lotus_report"] == "unavailable"
    assert body["normalized"]["policyVersionsBySource"]["lotus_core"] == "lotus-core-default-v1"
    assert body["normalized"]["policyVersionsBySource"]["lotus_performance"] == "unknown"
    assert body["normalized"]["policyVersionsBySource"]["lotus_report"] == "unknown"
    assert body["normalized"]["lotusCorePolicyDiagnostics"]["available"] is False
