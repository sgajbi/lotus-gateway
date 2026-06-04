from datetime import UTC, datetime
from typing import Any, cast

from app.contracts.risk_workspace import (
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.workbench import WorkbenchPartialFailure


def risk_upstream_failure(
    *,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchPartialFailure:
    detail = (
        str(upstream_payload.get("detail", upstream_payload))
        if isinstance(upstream_payload, dict)
        else str(upstream_payload)
    )
    return WorkbenchPartialFailure(
        source_service="risk",
        error_code=f"HTTP_{upstream_status}",
        detail=detail,
    )


def unavailable_risk_service_supportability(
    *,
    reason: str,
) -> list[WorkbenchRiskSupportabilityItem]:
    return [
        WorkbenchRiskSupportabilityItem(
            key="risk_service",
            label="Risk service",
            state="unavailable",
            reason=reason,
            source_service="lotus-risk",
        )
    ]


def risk_metadata(
    *,
    input_mode: str,
    cache_status: str,
    methodology_version: str | None = None,
) -> WorkbenchRiskMetadata:
    return WorkbenchRiskMetadata(
        generated_at=datetime.now(tz=UTC).isoformat(),
        input_mode=cast(Any, input_mode),
        cache_status=cast(Any, cache_status),
        methodology_version=methodology_version,
    )
