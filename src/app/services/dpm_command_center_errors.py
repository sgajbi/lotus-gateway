from typing import Any

from app.contracts.dpm_command_center import DpmOutcomeReviewErrorDetail
from app.services.upstream_envelope import raise_product_safe_upstream_error


def raise_manage_command_center_error(
    upstream_status: int,
    payload: dict[str, Any],
    *,
    error_code: str,
) -> None:
    raise_product_safe_upstream_error(
        upstream_status,
        payload,
        error_model=DpmOutcomeReviewErrorDetail,
        error_code=error_code,
        default_detail="lotus-manage command-center request failed",
    )
