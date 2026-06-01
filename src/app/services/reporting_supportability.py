from typing import Any, Protocol


class ReportingCapabilitiesClient(Protocol):
    async def get_capabilities(
        self,
        *,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        """Return lotus-report capability posture for a reporting consumer."""


class RenderMetadataClient(Protocol):
    async def get_metadata(self, *, correlation_id: str) -> tuple[int, dict[str, Any]]:
        """Return lotus-render metadata and supportability posture."""


def fallback_evidence_surface_supportability(reason: str) -> dict[str, Any]:
    return {
        "feature_key": "report.observability.evidence_surface_supportability",
        "state": "partial",
        "reason": reason,
        "freshness_bucket": "unknown",
        "evidence_feature_count": 0,
        "ready_evidence_feature_count": 0,
        "degraded_evidence_feature_count": 0,
        "workflow_count": 0,
        "ready_workflow_count": 0,
    }


def fallback_render_supportability(reason: str) -> dict[str, Any]:
    return {
        "feature_key": "render.observability.render_supportability",
        "state": "partial",
        "reason": reason,
        "freshness_bucket": "unknown",
        "deterministic_output_supported": False,
        "render_store_ready": False,
        "template_registry_ready": False,
        "default_output_format": None,
        "supported_output_formats": [],
    }


def normalize_render_supportability(payload: dict[str, Any]) -> dict[str, Any]:
    raw_supportability = payload.get("supportability")
    if not isinstance(raw_supportability, dict):
        return fallback_render_supportability("render_supportability_missing")

    supported_output_formats: list[str] = []
    raw_supported_output_formats = raw_supportability.get("supportedOutputFormats")
    if not isinstance(raw_supported_output_formats, list):
        raw_supported_output_formats = raw_supportability.get("supported_output_formats")
    if isinstance(raw_supported_output_formats, list):
        supported_output_formats = [str(item) for item in raw_supported_output_formats]

    return {
        **fallback_render_supportability("render_supportability_unknown"),
        "feature_key": str(
            raw_supportability.get("featureKey")
            or raw_supportability.get("feature_key")
            or "render.observability.render_supportability"
        ),
        "state": str(raw_supportability.get("state") or "partial"),
        "reason": str(raw_supportability.get("reason") or "render_supportability_unknown"),
        "freshness_bucket": str(
            raw_supportability.get("freshnessBucket")
            or raw_supportability.get("freshness_bucket")
            or "unknown"
        ),
        "deterministic_output_supported": _bool_value(
            _alias_value(
                raw_supportability,
                "deterministicOutputSupported",
                "deterministic_output_supported",
            )
        ),
        "render_store_ready": _bool_value(
            _alias_value(raw_supportability, "renderStoreReady", "render_store_ready")
        ),
        "template_registry_ready": _bool_value(
            _alias_value(
                raw_supportability,
                "templateRegistryReady",
                "template_registry_ready",
            )
        ),
        "default_output_format": raw_supportability.get("defaultOutputFormat")
        or raw_supportability.get("default_output_format"),
        "supported_output_formats": supported_output_formats,
    }


def normalize_evidence_surface_supportability(payload: dict[str, Any]) -> dict[str, Any]:
    raw_supportability = payload.get("supportability")
    if not isinstance(raw_supportability, dict):
        return fallback_evidence_surface_supportability("evidence_surface_supportability_missing")

    return {
        **fallback_evidence_surface_supportability("evidence_surface_supportability_unknown"),
        "feature_key": "report.observability.evidence_surface_supportability",
        "state": str(raw_supportability.get("state") or "partial"),
        "reason": str(
            raw_supportability.get("reason") or "evidence_surface_supportability_unknown"
        ),
        "freshness_bucket": str(
            raw_supportability.get("freshnessBucket")
            or raw_supportability.get("freshness_bucket")
            or "unknown"
        ),
        "evidence_feature_count": _non_negative_int(
            _alias_value(raw_supportability, "evidenceFeatureCount", "evidence_feature_count")
        ),
        "ready_evidence_feature_count": _non_negative_int(
            _alias_value(
                raw_supportability,
                "readyEvidenceFeatureCount",
                "ready_evidence_feature_count",
            )
        ),
        "degraded_evidence_feature_count": _non_negative_int(
            _alias_value(
                raw_supportability,
                "degradedEvidenceFeatureCount",
                "degraded_evidence_feature_count",
            )
        ),
        "workflow_count": _non_negative_int(
            _alias_value(raw_supportability, "workflowCount", "workflow_count")
        ),
        "ready_workflow_count": _non_negative_int(
            _alias_value(raw_supportability, "readyWorkflowCount", "ready_workflow_count")
        ),
    }


def _alias_value(payload: dict[str, Any], camel_case_key: str, snake_case_key: str) -> Any:
    if camel_case_key in payload:
        return payload[camel_case_key]
    return payload.get(snake_case_key)


def _non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, str):
        try:
            return max(int(value), 0)
        except ValueError:
            return 0
    return 0


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


async def get_evidence_surface_supportability(
    *,
    reporting_client: ReportingCapabilitiesClient,
    correlation_id: str,
    consumer_system: str,
    tenant_id: str | None,
) -> dict[str, Any]:
    status_code, payload = await reporting_client.get_capabilities(
        consumer_system=consumer_system,
        tenant_id=tenant_id or "default",
        correlation_id=correlation_id,
    )
    if status_code >= 400:
        return fallback_evidence_surface_supportability(
            "evidence_surface_supportability_unavailable"
        )
    return normalize_evidence_surface_supportability(payload)


async def attach_evidence_surface_supportability(
    payload: dict[str, Any],
    *,
    reporting_client: ReportingCapabilitiesClient,
    correlation_id: str,
    tenant_id: str | None,
) -> dict[str, Any]:
    try:
        supportability = await get_evidence_surface_supportability(
            reporting_client=reporting_client,
            correlation_id=correlation_id,
            consumer_system="lotus-gateway",
            tenant_id=tenant_id,
        )
    except Exception:
        supportability = fallback_evidence_surface_supportability(
            "evidence_surface_supportability_exception"
        )
    return {**payload, "supportability": supportability}


async def get_render_supportability(
    *,
    render_client: RenderMetadataClient,
    correlation_id: str,
) -> dict[str, Any]:
    status_code, payload = await render_client.get_metadata(correlation_id=correlation_id)
    if status_code >= 400:
        return fallback_render_supportability("render_supportability_unavailable")
    return normalize_render_supportability(payload)


async def attach_reporting_operator_supportability(
    payload: dict[str, Any],
    *,
    reporting_client: ReportingCapabilitiesClient,
    render_client: RenderMetadataClient,
    correlation_id: str,
    tenant_id: str | None,
) -> dict[str, Any]:
    with_evidence = await attach_evidence_surface_supportability(
        payload,
        reporting_client=reporting_client,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )
    try:
        render_supportability = await get_render_supportability(
            render_client=render_client,
            correlation_id=correlation_id,
        )
    except Exception:
        render_supportability = fallback_render_supportability("render_supportability_exception")
    return {**with_evidence, "render_supportability": render_supportability}
