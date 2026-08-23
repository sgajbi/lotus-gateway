import logging
from typing import Any

from fastapi import status

from app.contracts.dpm_pm_operating_quality import (
    DpmPmOperatingQualityErrorDetail,
    DpmPmOperatingQualityGatewayResponse,
)
from app.services import dpm_command_center_supportability
from app.services.dpm_pm_operating_quality_errors import (
    PmOperatingQualityValidationEvidence,
    extract_pm_operating_quality_validation_evidence,
)
from app.services.upstream_envelope import (
    build_upstream_status_gateway_envelope,
    raise_product_safe_upstream_error,
)

logger = logging.getLogger("analytics_ui.gateway")
_PM_OPERATING_QUALITY_OPERATION = "manage.rebalance.pm_operating_quality"
_PM_OPERATING_QUALITY_ERROR_CODE = "MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR"
_PM_OPERATING_QUALITY_DEFAULT_DETAIL = "lotus-manage command-center request failed"


def compose_pm_operating_quality_response(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    correlation_id: str,
) -> DpmPmOperatingQualityGatewayResponse:
    evidence = extract_pm_operating_quality_validation_evidence(
        upstream_status,
        upstream_payload,
    )
    if upstream_status >= status.HTTP_400_BAD_REQUEST:
        _log_pm_operating_quality_error(
            correlation_id=correlation_id,
            upstream_status=upstream_status,
            evidence=evidence,
        )
        raise_product_safe_upstream_error(
            upstream_status,
            upstream_payload,
            error_model=DpmPmOperatingQualityErrorDetail,
            error_code=_PM_OPERATING_QUALITY_ERROR_CODE,
            default_detail=_PM_OPERATING_QUALITY_DEFAULT_DETAIL,
            detail_fields={
                "reason_codes": list(evidence.reason_codes),
                "field_paths": list(evidence.field_paths),
            },
            detail_resolver=_pm_operating_quality_error_detail,
        )

    return build_upstream_status_gateway_envelope(
        DpmPmOperatingQualityGatewayResponse,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        supportability=dpm_command_center_supportability.pm_operating_quality_supportability_from(
            upstream_payload
        ),
        upstream_payload=upstream_payload,
    )


def _pm_operating_quality_error_detail(
    upstream_status: int,
    _upstream_payload: dict[str, Any],
    safe_detail: str,
) -> str:
    """Fail closed for PM-quality 5xx details while retaining safe 4xx codes."""

    if upstream_status >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        return _PM_OPERATING_QUALITY_DEFAULT_DETAIL
    return safe_detail


def _log_pm_operating_quality_error(
    *,
    correlation_id: str,
    upstream_status: int,
    evidence: PmOperatingQualityValidationEvidence,
) -> None:
    logger.warning(
        "gateway.manage.pm_operating_quality.upstream_error",
        extra={
            "extra_fields": {
                "event": "gateway.manage.pm_operating_quality.upstream_error",
                "service": "lotus-manage",
                "operation": _PM_OPERATING_QUALITY_OPERATION,
                "correlation_id": correlation_id,
                "upstream_status": upstream_status,
                "error_code": _PM_OPERATING_QUALITY_ERROR_CODE,
                "reason_codes": list(evidence.reason_codes),
                "field_paths": list(evidence.field_paths),
            }
        },
    )
