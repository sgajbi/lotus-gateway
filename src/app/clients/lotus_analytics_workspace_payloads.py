from typing import Any
from uuid import uuid4


def build_workspace_summary_payload(
    *,
    portfolio_id: str,
    report_end_date: str,
    report_start_date: str | None,
    period: str,
    chart_frequency: str,
    benchmark_id: str | None,
    reporting_currency: str | None,
    periods: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "calculation_id": str(uuid4()),
        "input_mode": "stateful",
        "portfolio_id": portfolio_id,
        "report_end_date": report_end_date,
        "periods": periods
        or _workspace_summary_periods(
            period=period,
            chart_frequency=chart_frequency,
            report_start_date=report_start_date,
        ),
        "include_benchmark": benchmark_id is not None,
        "stateful_input": {},
        "mwr_method": "XIRR",
    }
    if reporting_currency:
        payload["report_ccy"] = reporting_currency
    if report_start_date:
        payload["report_start_date"] = report_start_date
    if benchmark_id:
        payload["benchmark"] = _workspace_summary_benchmark(benchmark_id)
    return payload


def _workspace_summary_periods(
    *,
    period: str,
    chart_frequency: str,
    report_start_date: str | None,
) -> list[dict[str, Any]]:
    requested_period = "EXPLICIT" if report_start_date else period
    return [
        {
            "period": requested_period,
            "frequencies": _dedupe_frequencies([chart_frequency, "monthly", "quarterly", "yearly"]),
        }
    ]


def _workspace_summary_benchmark(benchmark_id: str) -> dict[str, Any]:
    return {
        "benchmark_id": benchmark_id,
        "input_mode": "stateful",
        "return_source": "calculated",
        "stateful_input": {},
    }


def _dedupe_frequencies(frequencies: list[str]) -> list[str]:
    deduped_frequencies: list[str] = []
    for frequency in frequencies:
        if frequency not in deduped_frequencies:
            deduped_frequencies.append(frequency)
    return deduped_frequencies
