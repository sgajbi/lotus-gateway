from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from app.contracts.risk_workspace import (
    RiskModuleState,
    RiskSupportabilityState,
    WorkbenchIssuerConcentration,
    WorkbenchPortfolioConcentration,
    WorkbenchRiskConcentrationExecutionContext,
    WorkbenchRiskConcentrationPayload,
    WorkbenchRiskConcentrationResponse,
    WorkbenchRiskConcentrationValuationContext,
    WorkbenchRiskMetadata,
    WorkbenchRiskSupportabilityItem,
    WorkbenchSinglePositionConcentration,
)
from app.contracts.workbench import WorkbenchPartialFailure
from app.services.source_supportability import (
    extract_calculation_supportability,
    source_supportability_reason,
)


@dataclass(frozen=True)
class ConcentrationBlocks:
    portfolio: dict[str, Any]
    single_position: dict[str, Any]
    issuer: dict[str, Any]


def map_concentration_response(
    *,
    correlation_id: str,
    portfolio_id: str,
    period: str,
    as_of_date: str,
    benchmark_code: str | None,
    upstream_payload: dict[str, Any],
) -> WorkbenchRiskConcentrationResponse:
    concentration_blocks, missing_blocks = _extract_concentration_blocks(upstream_payload)
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
    supportability = _build_concentration_supportability(
        blocks=concentration_blocks,
        upstream_payload=upstream_payload,
    )
    _append_source_calculation_supportability(
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
        supportability=[
            WorkbenchRiskSupportabilityItem(
                key="risk_service",
                label="Risk service",
                state="unavailable",
                reason="lotus-risk concentration endpoint is unavailable.",
                source_service="lotus-risk",
            )
        ],
        warnings=["RISK_CONCENTRATION_UNAVAILABLE"],
        partial_failures=[_upstream_failure(upstream_status, upstream_payload)],
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
                source_service="risk",
                error_code="MALFORMED_RISK_CONCENTRATION",
                detail=detail,
            )
        ],
        metadata=_metadata(input_mode="stateful", cache_status="miss"),
    )


def _extract_concentration_blocks(
    upstream_payload: dict[str, Any],
) -> tuple[ConcentrationBlocks | None, list[str]]:
    block_payloads = {
        "portfolio_concentration": upstream_payload.get("risk_proxy"),
        "single_position_concentration": upstream_payload.get("single_position_concentration"),
        "issuer_concentration": upstream_payload.get("issuer_concentration"),
    }
    missing_blocks = [key for key, value in block_payloads.items() if not isinstance(value, dict)]
    if missing_blocks:
        return None, missing_blocks
    return (
        ConcentrationBlocks(
            portfolio=cast(dict[str, Any], block_payloads["portfolio_concentration"]),
            single_position=cast(
                dict[str, Any],
                block_payloads["single_position_concentration"],
            ),
            issuer=cast(dict[str, Any], block_payloads["issuer_concentration"]),
        ),
        [],
    )


def _build_concentration_supportability(
    *,
    blocks: ConcentrationBlocks,
    upstream_payload: dict[str, Any],
) -> list[WorkbenchRiskSupportabilityItem]:
    return [
        WorkbenchRiskSupportabilityItem(
            key="portfolio_positions",
            label="Portfolio positions",
            state="ready",
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="issuer_enrichment",
            label="Issuer enrichment",
            state=_issuer_supportability_state(blocks.issuer),
            reason=_issuer_supportability_reason(blocks.issuer),
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="issuer_grouping",
            label="Issuer grouping",
            state="ready",
            reason=_issuer_grouping_reason(upstream_payload.get("metadata")),
            source_service="lotus-risk",
        ),
        WorkbenchRiskSupportabilityItem(
            key="valuation_basis",
            label="Valuation basis",
            state="ready",
            reason=_valuation_context_reason(upstream_payload.get("valuation_context")),
            source_service="lotus-risk",
        ),
    ]


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


def _issuer_supportability_state(payload: Any) -> RiskSupportabilityState:
    if not isinstance(payload, dict):
        return "unavailable"
    status_value = str(payload.get("coverage_status", "")).lower()
    if status_value == "complete":
        return "ready"
    if status_value == "partial":
        return "partial"
    return "unavailable"


def _issuer_supportability_reason(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return "Issuer concentration block was not returned by lotus-risk."
    note = payload.get("note")
    if isinstance(note, str) and note.strip():
        return note
    if str(payload.get("coverage_status", "")).lower() != "complete":
        return "Issuer coverage is not complete for the selected portfolio context."
    return None


def _issuer_grouping_reason(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "Issuer grouping metadata was not returned by lotus-risk."
    grouping = payload.get("issuer_grouping_level")
    policy = payload.get("enrichment_policy")
    grouping_label = str(grouping).replace("_", " ") if grouping else "unspecified grouping"
    policy_label = str(policy).replace("_", " ") if policy else "unspecified policy"
    return f"{grouping_label.title()} grouping with {policy_label} enrichment policy."


def _valuation_context_reason(payload: Any) -> str:
    if not isinstance(payload, dict):
        return "Valuation context was not returned by lotus-risk."
    reporting_currency = payload.get("reporting_currency")
    portfolio_currency = payload.get("portfolio_currency")
    weight_basis = payload.get("weight_basis")
    basis_label = str(weight_basis).replace("_", " ") if weight_basis else "reported weights"
    currency_context = " / ".join(
        part
        for part in [
            str(reporting_currency) if reporting_currency else None,
            str(portfolio_currency) if portfolio_currency else None,
        ]
        if part
    )
    if currency_context:
        return f"{basis_label.title()} in {currency_context} context."
    return f"{basis_label.title()} context."


def _append_source_calculation_supportability(
    *,
    supportability: list[WorkbenchRiskSupportabilityItem],
    upstream_payload: dict[str, Any],
) -> None:
    source_supportability = extract_calculation_supportability(upstream_payload)
    if source_supportability is None:
        return

    supportability.append(
        WorkbenchRiskSupportabilityItem(
            key="source_calculation",
            label="Source calculation",
            state=cast(Any, source_supportability.risk_contract_state),
            reason=source_supportability_reason(
                source_supportability,
                default_ready_reason="Source calculation supportability was confirmed upstream.",
            ),
            source_service=source_supportability.source_service or "lotus-risk",
        )
    )


def _upstream_failure(upstream_status: int, upstream_payload: Any) -> WorkbenchPartialFailure:
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


def _metadata(*, input_mode: str, cache_status: str) -> WorkbenchRiskMetadata:
    return WorkbenchRiskMetadata(
        generated_at=datetime.now(tz=UTC).isoformat(),
        input_mode=cast(Any, input_mode),
        cache_status=cast(Any, cache_status),
        methodology_version="lotus-risk",
    )
