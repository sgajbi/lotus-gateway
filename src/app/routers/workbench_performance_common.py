from fastapi import Query

from app.routers.workbench_caller_context import (
    WORKBENCH_CALLER_OPENAPI,
    UnambiguousWorkbenchCallerContext,
)

# Admission retains the established product-safe 400 response while the served
# contract explicitly describes the required trusted-context trio.
PERFORMANCE_CALLER_OPENAPI = WORKBENCH_CALLER_OPENAPI
PerformanceCallerContext = UnambiguousWorkbenchCallerContext

PERFORMANCE_PERIOD_DESCRIPTION = (
    "Canonical performance horizon: MTD, QTD, YTD, 1Y, 2Y, 3Y, 5Y, or 10Y; SI requires "
    "source-owned inception metadata; EXPLICIT requires report_start_date. Unknown or malformed "
    "periods and dates return a typed 422 response."
)

PERIOD_QUERY = Query(default="YTD", description=PERFORMANCE_PERIOD_DESCRIPTION, examples=["YTD"])

AS_OF_DATE_QUERY = Query(
    default=None,
    pattern=r"^\d{4}-\d{2}-\d{2}$",
    description=(
        "Optional review as-of date. When report_end_date is omitted, this date anchors "
        "the performance workspace window."
    ),
    examples=["2026-04-10"],
)
REPORTING_CURRENCY_QUERY = Query(
    default=None,
    min_length=3,
    max_length=3,
    pattern=r"^[A-Za-z]{3}$",
    description=(
        "Optional ISO 4217 reporting currency forwarded to lotus-performance for restatement."
    ),
    examples=["SGD"],
)
