from datetime import UTC, datetime
from typing import Any, Protocol, TypedDict, TypeVar, cast

from pydantic import BaseModel

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_envelope import RiskDetailBasis
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.upstream_envelope import safe_upstream_detail

RISK_SOURCE_SERVICE = "lotus-risk"


class RiskResponseIdentity(TypedDict):
    correlation_id: str
    portfolio_id: str
    period: str
    detail_basis: RiskDetailBasis
    as_of_date: str
    benchmark_code: str | None


class ReadyRiskResponseParts(Protocol):
    @property
    def state(self) -> RiskModuleState: ...

    @property
    def payload(self) -> Any: ...

    @property
    def warnings(self) -> list[str]: ...

    @property
    def partial_failures(self) -> list[WorkbenchPartialFailure]: ...

    @property
    def metadata(self) -> WorkbenchRiskMetadata: ...


RiskResponseT = TypeVar("RiskResponseT", bound=BaseModel)


def risk_response_identity(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    detail_basis: RiskDetailBasis,
    as_of_date: str,
    benchmark_code: str | None,
) -> RiskResponseIdentity:
    return {
        "correlation_id": correlation_id,
        "portfolio_id": portfolio_id,
        "period": period,
        "detail_basis": detail_basis,
        "as_of_date": as_of_date,
        "benchmark_code": benchmark_code,
    }


def ready_risk_response(
    response_model: type[RiskResponseT],
    *,
    identity: RiskResponseIdentity,
    parts: ReadyRiskResponseParts,
    supportability: list[WorkbenchRiskSupportabilityItem],
) -> RiskResponseT:
    return response_model(
        **identity,
        state=parts.state,
        payload=parts.payload,
        supportability=supportability,
        warnings=parts.warnings,
        partial_failures=parts.partial_failures,
        metadata=parts.metadata,
    )


def risk_upstream_failure(
    *,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchPartialFailure:
    detail = (
        safe_upstream_detail(upstream_payload, default_detail="risk request failed")
        if isinstance(upstream_payload, dict)
        else "risk request failed"
    )
    return WorkbenchPartialFailure(
        source_service=RISK_SOURCE_SERVICE,
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
            source_service=RISK_SOURCE_SERVICE,
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
