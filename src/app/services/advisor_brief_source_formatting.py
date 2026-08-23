from __future__ import annotations

from typing import Any

from app.contracts.advisor_brief import AdvisorBriefEvidenceRef
from app.contracts.performance_workspace import PerformanceWorkspaceResponse
from app.precision_policy import quantize_money, quantize_performance


def advisor_brief_summary_evidence_ref(
    *,
    label: str,
    value: str,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
    requested_as_of_date: str | None = None,
    requested_reporting_currency: str | None = None,
) -> AdvisorBriefEvidenceRef:
    return AdvisorBriefEvidenceRef(
        metric_label=label,
        metric_value=value,
        source_surface="performance.return_path",
        target_mode="summary",
        route=advisor_brief_route_query(
            portfolio_id=portfolio_id,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        ),
    )


def advisor_brief_analysis_evidence_ref(
    *,
    label: str,
    value: str,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
    requested_as_of_date: str | None = None,
    requested_reporting_currency: str | None = None,
) -> AdvisorBriefEvidenceRef:
    return AdvisorBriefEvidenceRef(
        metric_label=label,
        metric_value=value,
        source_surface="performance.contribution",
        target_mode="analysis",
        route=advisor_brief_route_query(
            portfolio_id=portfolio_id,
            period=period,
            basis=basis,
            benchmark_code=benchmark_code,
            requested_as_of_date=requested_as_of_date,
            requested_reporting_currency=requested_reporting_currency,
        ),
    )


def advisor_brief_route_query(
    *,
    portfolio_id: str,
    period: str,
    basis: str,
    benchmark_code: str | None,
    requested_as_of_date: str | None = None,
    requested_reporting_currency: str | None = None,
) -> str:
    route = f"/performance?portfolioId={portfolio_id}&period={period}&detailBasis={basis}"
    if benchmark_code:
        route += f"&benchmark={benchmark_code}"
    if requested_as_of_date:
        route += f"&asOfDate={requested_as_of_date}"
    if requested_reporting_currency:
        route += f"&reportingCurrency={requested_reporting_currency}"
    return route


def format_advisor_brief_pct(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{quantize_performance(value):.2f}%"


def format_advisor_brief_currency(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"${quantize_money(value):,.0f}"


def normalize_advisor_brief_position_label(position_id: str) -> str:
    display_label = position_id.rsplit(":", 1)[-1].strip()
    for prefix in ("FO_EQ_", "FO_FI_", "FO_CASH_", "FO_ALT_", "FO_FX_"):
        if display_label.startswith(prefix):
            display_label = display_label[len(prefix) :]
            break
    return display_label.replace("_", " ").strip() or position_id


def advisor_brief_portfolio_display_label(*, workspace: PerformanceWorkspaceResponse) -> str:
    return normalize_advisor_brief_position_label(workspace.portfolio.portfolio_id)


def advisor_brief_benchmark_display_label(
    *,
    workspace: PerformanceWorkspaceResponse,
) -> str | None:
    if not workspace.benchmark_code:
        return None
    for option in workspace.benchmark_options:
        if option.benchmark_code == workspace.benchmark_code:
            return option.benchmark_name.strip() or workspace.benchmark_code
    return workspace.benchmark_code
