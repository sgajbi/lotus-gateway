from typing import Any

import pytest

from app.services.reporting_supportability import (
    attach_reporting_operator_supportability,
    fallback_evidence_surface_supportability,
    fallback_render_supportability,
    normalize_evidence_surface_supportability,
    normalize_render_supportability,
)


class StubReportingClient:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self.payload = payload
        self.calls: list[dict[str, str]] = []

    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append(
            {
                "consumer_system": consumer_system,
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
            }
        )
        return self.status_code, self.payload


class StubRenderClient:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self.payload = payload
        self.calls: list[dict[str, str]] = []

    async def get_metadata(self, *, correlation_id: str) -> tuple[int, dict[str, Any]]:
        self.calls.append({"correlation_id": correlation_id})
        return self.status_code, self.payload


def test_normalize_evidence_surface_supportability_preserves_source_counts() -> None:
    normalized = normalize_evidence_surface_supportability(
        {
            "supportability": {
                "feature_key": "unexpected-source-key",
                "state": "ready",
                "reason": "evidence_surface_ready",
                "freshness_bucket": "current",
                "evidence_feature_count": 5,
                "ready_evidence_feature_count": 4,
            }
        }
    )

    assert normalized["feature_key"] == "report.observability.evidence_surface_supportability"
    assert normalized["state"] == "ready"
    assert normalized["reason"] == "evidence_surface_ready"
    assert normalized["evidence_feature_count"] == 5
    assert normalized["ready_evidence_feature_count"] == 4
    assert normalized["workflow_count"] == 0


def test_normalize_evidence_surface_supportability_accepts_camel_case_counts() -> None:
    normalized = normalize_evidence_surface_supportability(
        {
            "supportability": {
                "featureKey": "unexpected-source-key",
                "state": "ready",
                "reason": "evidence_surface_ready",
                "freshnessBucket": "current",
                "evidenceFeatureCount": "5",
                "readyEvidenceFeatureCount": 4,
                "degradedEvidenceFeatureCount": -1,
                "workflowCount": 3,
                "readyWorkflowCount": True,
            }
        }
    )

    assert normalized == {
        "feature_key": "report.observability.evidence_surface_supportability",
        "state": "ready",
        "reason": "evidence_surface_ready",
        "freshness_bucket": "current",
        "evidence_feature_count": 5,
        "ready_evidence_feature_count": 4,
        "degraded_evidence_feature_count": 0,
        "workflow_count": 3,
        "ready_workflow_count": 0,
    }


def test_normalize_evidence_surface_supportability_returns_safe_missing_fallback() -> None:
    expected = fallback_evidence_surface_supportability("evidence_surface_supportability_missing")

    assert normalize_evidence_surface_supportability({}) == expected


def test_normalize_render_supportability_accepts_camel_case_source_payload() -> None:
    normalized = normalize_render_supportability(
        {
            "supportability": {
                "featureKey": "render.custom",
                "state": "ready",
                "reason": "render_supportability_ready",
                "freshnessBucket": "current",
                "deterministicOutputSupported": True,
                "renderStoreReady": True,
                "templateRegistryReady": True,
                "defaultOutputFormat": "pdf",
                "supportedOutputFormats": ["pdf", "json"],
            }
        }
    )

    assert normalized == {
        "feature_key": "render.custom",
        "state": "ready",
        "reason": "render_supportability_ready",
        "freshness_bucket": "current",
        "deterministic_output_supported": True,
        "render_store_ready": True,
        "template_registry_ready": True,
        "default_output_format": "pdf",
        "supported_output_formats": ["pdf", "json"],
    }


def test_normalize_render_supportability_returns_safe_missing_fallback() -> None:
    assert normalize_render_supportability({}) == fallback_render_supportability(
        "render_supportability_missing"
    )


@pytest.mark.asyncio
async def test_attach_reporting_operator_supportability_uses_gateway_consumer_context() -> None:
    reporting_client = StubReportingClient(
        200,
        {
            "supportability": {
                "state": "ready",
                "reason": "evidence_surface_ready",
                "freshness_bucket": "current",
            }
        },
    )
    render_client = StubRenderClient(
        200,
        {
            "supportability": {
                "state": "ready",
                "reason": "render_supportability_ready",
                "freshness_bucket": "current",
            }
        },
    )

    response = await attach_reporting_operator_supportability(
        {"batch_id": "rbch_001"},
        reporting_client=reporting_client,
        render_client=render_client,
        correlation_id="corr-001",
        tenant_id="tenant-a",
    )

    assert response["batch_id"] == "rbch_001"
    assert response["supportability"]["reason"] == "evidence_surface_ready"
    assert response["render_supportability"]["reason"] == "render_supportability_ready"
    assert reporting_client.calls == [
        {
            "consumer_system": "lotus-gateway",
            "tenant_id": "tenant-a",
            "correlation_id": "corr-001",
        }
    ]
    assert render_client.calls == [{"correlation_id": "corr-001"}]


@pytest.mark.asyncio
async def test_attach_reporting_operator_supportability_falls_back_for_source_failures() -> None:
    response = await attach_reporting_operator_supportability(
        {"batch_id": "rbch_001"},
        reporting_client=StubReportingClient(503, {}),
        render_client=StubRenderClient(503, {}),
        correlation_id="corr-001",
        tenant_id=None,
    )

    assert response["supportability"] == fallback_evidence_surface_supportability(
        "evidence_surface_supportability_unavailable"
    )
    assert response["render_supportability"] == fallback_render_supportability(
        "render_supportability_unavailable"
    )
