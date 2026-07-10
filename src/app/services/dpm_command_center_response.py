from typing import Any

from app.contracts.dpm_command_center import (
    DpmCommandCenterGatewayResponse,
    DpmOutcomeReviewErrorDetail,
    DpmOutcomeReviewGatewayResponse,
    DpmPortfolioMemoryGatewayResponse,
)
from app.services import dpm_command_center_supportability
from app.services.upstream_envelope import build_product_safe_upstream_status_gateway_envelope


def compose_outcome_review_response(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    correlation_id: str,
) -> DpmOutcomeReviewGatewayResponse:
    return build_product_safe_upstream_status_gateway_envelope(
        DpmOutcomeReviewGatewayResponse,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        supportability=dpm_command_center_supportability.outcome_review_supportability_from(
            upstream_payload
        ),
        upstream_payload=upstream_payload,
        error_model=DpmOutcomeReviewErrorDetail,
        error_code="MANAGE_OUTCOME_REVIEW_UPSTREAM_ERROR",
        default_detail="lotus-manage command-center request failed",
    )


def compose_command_center_response(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    correlation_id: str,
) -> DpmCommandCenterGatewayResponse:
    return build_product_safe_upstream_status_gateway_envelope(
        DpmCommandCenterGatewayResponse,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        supportability=dpm_command_center_supportability.command_center_supportability_from(
            upstream_payload
        ),
        upstream_payload=upstream_payload,
        error_model=DpmOutcomeReviewErrorDetail,
        error_code="MANAGE_COMMAND_CENTER_UPSTREAM_ERROR",
        default_detail="lotus-manage command-center request failed",
    )


def compose_portfolio_memory_response(
    upstream_status: int,
    upstream_payload: dict[str, Any],
    correlation_id: str,
) -> DpmPortfolioMemoryGatewayResponse:
    return build_product_safe_upstream_status_gateway_envelope(
        DpmPortfolioMemoryGatewayResponse,
        correlation_id=correlation_id,
        upstream_status=upstream_status,
        supportability=dpm_command_center_supportability.portfolio_memory_supportability_from(
            upstream_payload
        ),
        upstream_payload=upstream_payload,
        error_model=DpmOutcomeReviewErrorDetail,
        error_code="MANAGE_PORTFOLIO_MEMORY_UPSTREAM_ERROR",
        default_detail="lotus-manage command-center request failed",
    )
