from typing import Annotated

from fastapi import Query

RISK_PERIOD_QUERY_DESCRIPTION = (
    "Canonical risk horizon. Use platform-governed values such as MTD, QTD, YTD, 1Y, 3Y, 5Y, "
    "SI, YEAR, or EXPLICIT. Legacy aliases ONE_YEAR, THREE_YEAR, FIVE_YEAR, and ITD may be "
    "accepted for compatibility but are normalized before calling lotus-risk."
)

RiskPeriodQuery = Annotated[
    str,
    Query(
        description=RISK_PERIOD_QUERY_DESCRIPTION,
        examples=["YTD"],
    ),
]
RiskSummaryDetailBasisQuery = Annotated[
    str,
    Query(
        description="Requested net or gross basis for the risk summary metrics.",
        examples=["NET"],
    ),
]
RiskAttributionDetailBasisQuery = Annotated[
    str,
    Query(
        description="Requested net or gross basis for risk attribution metrics.",
        examples=["NET"],
    ),
]
RiskSummaryBenchmarkCodeQuery = Annotated[
    str | None,
    Query(
        description="Optional benchmark override used for relative risk context.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    ),
]
RiskAttributionBenchmarkCodeQuery = Annotated[
    str | None,
    Query(
        description="Optional benchmark override used for relative attribution context.",
        examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
    ),
]
RiskAsOfDateQuery = Annotated[
    str | None,
    Query(
        description="Optional business as-of date in YYYY-MM-DD format.",
        examples=["2026-02-24"],
    ),
]
RiskReportStartDateQuery = Annotated[
    str | None,
    Query(
        description=(
            "Inclusive explicit start date when the caller requests an explicit risk window."
        ),
        examples=["2026-01-01"],
    ),
]
RiskReportEndDateQuery = Annotated[
    str | None,
    Query(
        description="Inclusive explicit end date when the caller requests an explicit risk window.",
        examples=["2026-03-27"],
    ),
]
RiskSummaryReportingCurrencyQuery = Annotated[
    str,
    Query(
        description="Reporting currency used for stateful risk and risk-free-rate sourcing.",
        examples=["USD"],
    ),
]
RiskAttributionReportingCurrencyQuery = Annotated[
    str,
    Query(
        description="Reporting currency used for stateful risk attribution analytics.",
        examples=["USD"],
    ),
]
