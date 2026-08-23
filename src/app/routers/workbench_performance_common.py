from fastapi import Query

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
