from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "WorkbenchIssuerConcentration",
    "WorkbenchPortfolioConcentration",
    "WorkbenchRiskConcentrationExecutionContext",
    "WorkbenchRiskConcentrationPayload",
    "WorkbenchRiskConcentrationValuationContext",
    "WorkbenchSinglePositionConcentration",
    "WorkbenchTopIssuerDriver",
    "WorkbenchTopPositionDriver",
]

_RISK_CONCENTRATION_PAYLOAD_EXAMPLE: dict[str, Any] = {
    "portfolio_concentration": {
        "hhi_current": 1200.0,
        "hhi_proposed": 1225.0,
        "hhi_delta": 25.0,
    },
    "single_position_concentration": {
        "top_position_weight_current": 0.2,
        "top_position_weight_proposed": 0.21,
        "top_position_weight_delta": 0.01,
        "top_n_cumulative_weight_current": 0.5,
        "top_n_cumulative_weight_proposed": 0.52,
        "top_n_cumulative_weight_delta": 0.02,
        "top_n": 10,
        "top_position_current": {
            "security_id": "FO_FUND_PIMCO_INC",
            "security_name": "PIMCO GIS Income Fund",
            "weight": 0.2,
        },
        "top_position_proposed": {
            "security_id": "FO_FUND_PIMCO_INC",
            "security_name": "PIMCO GIS Income Fund",
            "weight": 0.21,
        },
    },
    "issuer_concentration": {
        "hhi_current": 1500.0,
        "hhi_proposed": 1600.0,
        "hhi_delta": 100.0,
        "top_issuer_weight_current": 0.25,
        "top_issuer_weight_proposed": 0.27,
        "top_issuer_weight_delta": 0.02,
        "coverage_status": "complete",
        "covered_position_count_current": 10,
        "covered_position_count_proposed": 10,
        "total_position_count_current": 10,
        "total_position_count_proposed": 10,
        "uncovered_position_count_current": 0,
        "uncovered_position_count_proposed": 0,
        "coverage_ratio_current": 1.0,
        "coverage_ratio_proposed": 1.0,
        "note": None,
        "top_issuer_current": {
            "issuer_id": "ULTIMATE_PIMCO",
            "issuer_name": "Pacific Investment Management Company LLC",
            "weight": 0.25,
        },
        "top_issuer_proposed": {
            "issuer_id": "ULTIMATE_PIMCO",
            "issuer_name": "Pacific Investment Management Company LLC",
            "weight": 0.27,
        },
    },
    "valuation_context": {
        "portfolio_currency": "USD",
        "reporting_currency": "USD",
        "position_basis": "market_value_base",
        "weight_basis": "total_market_value_base",
    },
    "execution_context": {
        "as_of_date": "2026-04-04",
        "portfolio_id": "PF_RISK_CONC",
        "simulation_session_id": None,
        "simulation_session_version": None,
        "session_expires_at": None,
        "issuer_grouping_level": "ultimate_parent",
        "enrichment_policy": "merge_caller_then_core",
        "include_cash_positions": True,
        "include_zero_quantity_positions": False,
    },
}


class WorkbenchPortfolioConcentration(BaseModel):
    hhi_current: float = Field(
        description="Current portfolio Herfindahl-Hirschman concentration index.",
        examples=[1200.0],
    )
    hhi_proposed: float = Field(
        description="Projected portfolio Herfindahl-Hirschman concentration index.",
        examples=[1225.0],
    )
    hhi_delta: float = Field(
        description="Delta between projected and current portfolio concentration index.",
        examples=[25.0],
    )


class WorkbenchTopPositionDriver(BaseModel):
    security_id: str | None = Field(
        default=None,
        description="Optional security identifier for the top-position concentration driver.",
        examples=["FO_FUND_PIMCO_INC"],
    )
    security_name: str | None = Field(
        default=None,
        description="Security display name for the top-position concentration driver.",
        examples=["PIMCO GIS Income Fund"],
    )
    weight: float = Field(
        description="Portfolio weight of the identified top position.",
        examples=[0.2],
    )


class WorkbenchSinglePositionConcentration(BaseModel):
    top_position_weight_current: float = Field(
        description="Current portfolio weight of the single largest position.",
        examples=[0.2],
    )
    top_position_weight_proposed: float = Field(
        description="Projected portfolio weight of the single largest position.",
        examples=[0.21],
    )
    top_position_weight_delta: float = Field(
        description="Delta between projected and current top-position weight.",
        examples=[0.01],
    )
    top_n_cumulative_weight_current: float = Field(
        description="Current cumulative weight of the top-N largest positions.",
        examples=[0.5],
    )
    top_n_cumulative_weight_proposed: float = Field(
        description="Projected cumulative weight of the top-N largest positions.",
        examples=[0.52],
    )
    top_n_cumulative_weight_delta: float = Field(
        description="Delta between projected and current cumulative top-N position weight.",
        examples=[0.02],
    )
    top_n: int = Field(
        description="Number of largest positions included in the cumulative concentration lens.",
        examples=[10],
    )
    top_position_current: WorkbenchTopPositionDriver = Field(
        description="Current largest position driving single-name concentration.",
    )
    top_position_proposed: WorkbenchTopPositionDriver = Field(
        description="Projected largest position driving single-name concentration.",
    )


class WorkbenchTopIssuerDriver(BaseModel):
    issuer_id: str | None = Field(
        default=None,
        description="Optional issuer identifier for the top issuer concentration driver.",
        examples=["ULTIMATE_PIMCO"],
    )
    issuer_name: str | None = Field(
        default=None,
        description="Issuer display name for the top issuer concentration driver.",
        examples=["Pacific Investment Management Company LLC"],
    )
    weight: float = Field(
        description="Portfolio weight mapped to the top issuer.",
        examples=[0.25],
    )


class WorkbenchIssuerConcentration(BaseModel):
    hhi_current: float = Field(
        description="Current issuer-level Herfindahl-Hirschman concentration index.",
        examples=[1500.0],
    )
    hhi_proposed: float = Field(
        description="Projected issuer-level Herfindahl-Hirschman concentration index.",
        examples=[1600.0],
    )
    hhi_delta: float = Field(
        description="Delta between projected and current issuer concentration index.",
        examples=[100.0],
    )
    top_issuer_weight_current: float = Field(
        description="Current portfolio weight mapped to the single largest issuer exposure.",
        examples=[0.25],
    )
    top_issuer_weight_proposed: float = Field(
        description="Projected portfolio weight mapped to the single largest issuer exposure.",
        examples=[0.27],
    )
    top_issuer_weight_delta: float = Field(
        description="Delta between projected and current top-issuer portfolio weight.",
        examples=[0.02],
    )
    coverage_status: str = Field(
        description="Issuer enrichment coverage status returned by lotus-risk.",
        examples=["complete"],
    )
    covered_position_count_current: int = Field(
        description="Current number of positions successfully mapped into issuer analysis.",
        examples=[10],
    )
    covered_position_count_proposed: int = Field(
        description="Projected number of positions successfully mapped into issuer analysis.",
        examples=[10],
    )
    total_position_count_current: int = Field(
        description="Current total position count evaluated for issuer enrichment.",
        examples=[10],
    )
    total_position_count_proposed: int = Field(
        description="Projected total position count evaluated for issuer enrichment.",
        examples=[10],
    )
    uncovered_position_count_current: int = Field(
        description="Current number of positions not mapped into issuer analysis.",
        examples=[0],
    )
    uncovered_position_count_proposed: int = Field(
        description="Projected number of positions not mapped into issuer analysis.",
        examples=[0],
    )
    coverage_ratio_current: float = Field(
        description="Current share of positions covered by issuer enrichment.",
        examples=[1.0],
    )
    coverage_ratio_proposed: float = Field(
        description="Projected share of positions covered by issuer enrichment.",
        examples=[1.0],
    )
    note: str | None = Field(
        default=None,
        description="Optional issuer coverage note from lotus-risk.",
        examples=[None],
    )
    top_issuer_current: WorkbenchTopIssuerDriver = Field(
        description="Current issuer driving the largest mapped issuer concentration exposure.",
    )
    top_issuer_proposed: WorkbenchTopIssuerDriver = Field(
        description="Projected issuer driving the largest mapped issuer concentration exposure.",
    )


class WorkbenchRiskConcentrationValuationContext(BaseModel):
    portfolio_currency: str | None = Field(
        default=None,
        description="Portfolio base currency used for the concentration valuation context.",
        examples=["USD"],
    )
    reporting_currency: str | None = Field(
        default=None,
        description="Reporting currency applied to the concentration calculation when overridden.",
        examples=["USD"],
    )
    position_basis: str | None = Field(
        default=None,
        description="Position valuation basis used for the concentration calculation.",
        examples=["market_value_base"],
    )
    weight_basis: str | None = Field(
        default=None,
        description="Weight denominator used by lotus-risk for the concentration output.",
        examples=["total_market_value_base"],
    )


class WorkbenchRiskConcentrationExecutionContext(BaseModel):
    as_of_date: str | None = Field(
        default=None,
        description="Resolved as-of date used by lotus-risk for the concentration request.",
        examples=["2026-04-04"],
    )
    portfolio_id: str | None = Field(
        default=None,
        description="Portfolio identifier echoed by lotus-risk in the execution context.",
        examples=["PF_RISK_CONC"],
    )
    simulation_session_id: str | None = Field(
        default=None,
        description=(
            "Optional sandbox session identifier when simulation concentration is supported."
        ),
        examples=["sess_1"],
    )
    simulation_session_version: int | None = Field(
        default=None,
        description=(
            "Optional sandbox session version when simulation concentration is supported."
        ),
        examples=[2],
    )
    session_expires_at: str | None = Field(
        default=None,
        description=(
            "Optional sandbox session expiry timestamp when simulation concentration is supported."
        ),
        examples=["2026-04-05T08:15:00Z"],
    )
    issuer_grouping_level: str = Field(
        description="Issuer grouping level applied by lotus-risk for concentration rollups.",
        examples=["ultimate_parent"],
    )
    enrichment_policy: str = Field(
        description="Issuer enrichment policy applied by lotus-risk.",
        examples=["merge_caller_then_core"],
    )
    include_cash_positions: bool | None = Field(
        default=None,
        description="Whether cash positions were included in the concentration calculation.",
        examples=[True],
    )
    include_zero_quantity_positions: bool | None = Field(
        default=None,
        description=(
            "Whether zero-quantity positions were included in the concentration calculation."
        ),
        examples=[False],
    )


class WorkbenchRiskConcentrationPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": cast(Any, _RISK_CONCENTRATION_PAYLOAD_EXAMPLE)}
    )

    portfolio_concentration: WorkbenchPortfolioConcentration = Field(
        description="Portfolio-level HHI concentration metrics for the current and projected book.",
    )
    single_position_concentration: WorkbenchSinglePositionConcentration = Field(
        description="Largest position and top-N single-name concentration metrics.",
    )
    issuer_concentration: WorkbenchIssuerConcentration = Field(
        description="Issuer-grouped concentration metrics and enrichment coverage posture.",
    )
    valuation_context: WorkbenchRiskConcentrationValuationContext | None = Field(
        default=None,
        description="Valuation-basis context carried with the concentration calculation.",
    )
    execution_context: WorkbenchRiskConcentrationExecutionContext | None = Field(
        default=None,
        description="Execution metadata describing how lotus-risk ran the concentration request.",
    )
