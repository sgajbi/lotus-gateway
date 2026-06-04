from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, Query

from app.routers.workbench_caller_context import require_workbench_caller_context

PERIOD_QUERY = Query(
    default="YTD",
    description=(
        "Requested advisor-brief horizon. Use canonical values such as YTD or EXPLICIT when "
        "paired with report dates."
    ),
    examples=["YTD"],
)
CHART_FREQUENCY_QUERY = Query(
    default="monthly",
    description="Requested workspace frequency context used to source the advisor brief.",
    examples=["monthly"],
)
CONTRIBUTION_DIMENSION_QUERY = Query(
    default="asset_class",
    description="Requested contribution dimension used to source the advisor brief context.",
    examples=["asset_class"],
)
ATTRIBUTION_DIMENSION_QUERY = Query(
    default="asset_class",
    description="Requested attribution dimension used to source the advisor brief context.",
    examples=["asset_class"],
)
DETAIL_BASIS_QUERY = Query(
    default="NET",
    description="Performance basis requested for the advisor brief analytics.",
    examples=["NET"],
)
BENCHMARK_CODE_QUERY = Query(
    default=None,
    description=(
        "Optional benchmark override. When omitted, the portfolio-assigned benchmark is used "
        "when available."
    ),
    examples=["BMK_PB_GLOBAL_BALANCED_60_40"],
)
REPORT_START_DATE_QUERY = Query(
    default=None,
    description="Inclusive explicit start date for an EXPLICIT advisor-brief window.",
    examples=["2026-01-01"],
)
REPORT_END_DATE_QUERY = Query(
    default=None,
    description="Inclusive explicit end date for an EXPLICIT advisor-brief window.",
    examples=["2026-04-04"],
)


@dataclass(frozen=True)
class AdvisorBriefQuery:
    period: str
    chart_frequency: str
    contribution_dimension: str
    attribution_dimension: str
    detail_basis: str
    benchmark_code: str | None
    report_start_date: str | None
    report_end_date: str | None


def require_advisor_brief_caller_context(
    *,
    actor_id: str | None,
    caller_application: str | None,
    tenant_id: str | None,
    region: str | None,
    booking_center_code: str | None,
    role: str | None,
) -> dict[str, str]:
    return require_workbench_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )


def build_advisor_brief_query(
    period: str = PERIOD_QUERY,
    chart_frequency: str = CHART_FREQUENCY_QUERY,
    contribution_dimension: str = CONTRIBUTION_DIMENSION_QUERY,
    attribution_dimension: str = ATTRIBUTION_DIMENSION_QUERY,
    detail_basis: str = DETAIL_BASIS_QUERY,
    benchmark_code: str | None = BENCHMARK_CODE_QUERY,
    report_start_date: str | None = REPORT_START_DATE_QUERY,
    report_end_date: str | None = REPORT_END_DATE_QUERY,
) -> AdvisorBriefQuery:
    return AdvisorBriefQuery(
        period=period,
        chart_frequency=chart_frequency,
        contribution_dimension=contribution_dimension,
        attribution_dimension=attribution_dimension,
        detail_basis=detail_basis,
        benchmark_code=benchmark_code,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
    )


def require_advisor_brief_caller_context_dependency(
    actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    caller_application: Annotated[str | None, Header(alias="X-Caller-Application")] = None,
    tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
    region: Annotated[str | None, Header(alias="X-Region")] = None,
    booking_center_code: Annotated[str | None, Header(alias="X-Booking-Center-Code")] = None,
    role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> dict[str, str]:
    return require_advisor_brief_caller_context(
        actor_id=actor_id,
        caller_application=caller_application,
        tenant_id=tenant_id,
        region=region,
        booking_center_code=booking_center_code,
        role=role,
    )
