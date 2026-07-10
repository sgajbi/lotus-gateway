from typing import Any

from app.contracts.risk_workspace import (
    RiskModuleState,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
)
from app.contracts.risk_workspace_concentration import (
    WorkbenchIssuerConcentration,
    WorkbenchPortfolioConcentration,
    WorkbenchRiskConcentrationExecutionContext,
    WorkbenchRiskConcentrationPayload,
    WorkbenchRiskConcentrationValuationContext,
    WorkbenchSinglePositionConcentration,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.risk_workspace_concentration_supportability import (
    ConcentrationBlocks,
    append_source_calculation_supportability,
    build_concentration_supportability,
    extract_concentration_blocks,
)
from app.services.risk_workspace_envelopes import (
    RISK_SOURCE_SERVICE,
    risk_metadata,
    risk_upstream_failure,
    unavailable_risk_service_supportability,
)


def map_concentration_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskConcentrationResponse:
    concentration_blocks, missing_blocks = extract_concentration_blocks(upstream_payload)
    if missing_blocks:
        return malformed_concentration(
            correlation_id=correlation_id,
            portfolio_id=portfolio_id,
            period=period,
            as_of_date=as_of_date,
            benchmark_code=benchmark_code,
            missing_blocks=missing_blocks,
        )
    assert concentration_blocks is not None
    supportability = build_concentration_supportability(
        blocks=concentration_blocks,
        upstream_payload=upstream_payload,
    )
    append_source_calculation_supportability(
        supportability=supportability,
        upstream_payload=upstream_payload,
    )
    return WorkbenchRiskConcentrationResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state=_concentration_response_state(supportability),
        payload=_build_concentration_payload(
            blocks=concentration_blocks,
            upstream_payload=upstream_payload,
        ),
        supportability=supportability,
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def unavailable_concentration(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_status: int,
    upstream_payload: Any,
) -> WorkbenchRiskConcentrationResponse:
    return WorkbenchRiskConcentrationResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=None,
        supportability=unavailable_risk_service_supportability(
            reason="lotus-risk concentration endpoint is unavailable."
        ),
        warnings=["RISK_CONCENTRATION_UNAVAILABLE"],
        partial_failures=[
            risk_upstream_failure(
                upstream_status=upstream_status,
                upstream_payload=upstream_payload,
            )
        ],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def malformed_concentration(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    missing_blocks: list[str],
) -> WorkbenchRiskConcentrationResponse:
    detail = "lotus-risk concentration response omitted required blocks: " + ", ".join(
        missing_blocks
    )
    return WorkbenchRiskConcentrationResponse(
        correlation_id=correlation_id,
        portfolio_id=portfolio_id,
        period=period,
        as_of_date=as_of_date,
        benchmark_code=benchmark_code,
        state="unavailable",
        payload=None,
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service_contract",
                label="Risk service contract",
                state="unavailable",
                reason=detail,
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_CONCENTRATION_CONTRACT_INVALID"],
        partial_failures=[
            WorkbenchPartialFailure(
                source_service=RISK_SOURCE_SERVICE,
                error_code="MALFORMED_RISK_CONCENTRATION",
                detail=detail,
            )
        ],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _build_concentration_payload(
    *,
    blocks: ConcentrationBlocks,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskConcentrationPayload:
    valuation_context = upstream_payload.get("valuation_context")
    execution_context = upstream_payload.get("metadata")
    return WorkbenchRiskConcentrationPayload(
        portfolio_concentration=WorkbenchPortfolioConcentration.model_validate(blocks.portfolio),
        single_position_concentration=WorkbenchSinglePositionConcentration.model_validate(
            blocks.single_position
        ),
        issuer_concentration=WorkbenchIssuerConcentration.model_validate(blocks.issuer),
        valuation_context=WorkbenchRiskConcentrationValuationContext.model_validate(
            valuation_context
        )
        if isinstance(valuation_context, dict)
        else None,
        execution_context=WorkbenchRiskConcentrationExecutionContext.model_validate(
            execution_context
        )
        if isinstance(execution_context, dict)
        else None,
    )


def _concentration_response_state(
    supportability: list[WorkbenchRiskSupportabilityItem],
) -> RiskModuleState:
    return "ready" if all(item.state == "ready" for item in supportability) else "partial"


def _metadata(*, input_mode: str, cache_status: str) -> WorkbenchRiskMetadata:
    return risk_metadata(
        input_mode=input_mode,
        cache_status=cache_status,
        methodology_version="lotus-risk",
    )
