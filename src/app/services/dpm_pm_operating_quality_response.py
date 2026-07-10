from typing import Any

from app.contracts.dpm_command_center import (
    DpmOutcomeReviewErrorDetail,
    DpmPmOperatingQualityGatewayResponse,
)
from app.services import dpm_command_center_supportability
from app.services.upstream_envelope import build_product_safe_upstream_status_gateway_envelope


def compose_pm_operating_quality_response(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    correlation_id: str,
) -> DpmPmOperatingQualityGatewayResponse:
    return build_product_safe_upstream_status_gateway_envelope(
        DpmPmOperatingQualityGatewayResponse,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        supportability=dpm_command_center_supportability.pm_operating_quality_supportability_from(
            upstream_payload
        ),
        upstream_payload=upstream_payload,
        error_model=DpmOutcomeReviewErrorDetail,
        error_code="MANAGE_PM_OPERATING_QUALITY_UPSTREAM_ERROR",
        default_detail="lotus-manage command-center request failed",
    )
