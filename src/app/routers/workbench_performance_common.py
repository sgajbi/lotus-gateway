from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request

from app.routers.workbench_caller_context import require_workbench_caller_context

# Admission retains the established product-safe 400 response while the served
# contract explicitly describes the required trusted-context trio.
PERFORMANCE_CALLER_OPENAPI = {
    "parameters": [
        {
            "name": name,
            "in": "header",
            "required": name in {"X-Actor-Id", "X-Tenant-Id", "X-Region"},
            "description": "Admitted trusted caller context; not a production IAM grant.",
            "schema": {"type": "string", "minLength": 1, "pattern": r".*\S.*"},
        }
        for name in (
            "X-Actor-Id",
            "X-Tenant-Id",
            "X-Region",
            "X-Caller-Application",
            "X-Booking-Center-Code",
            "X-Role",
        )
    ]
}


def require_performance_caller_context(request: Request) -> dict[str, str]:
    """Reuse trusted admission and reject ambiguous wire identities before source I/O."""
    for parameter in PERFORMANCE_CALLER_OPENAPI["parameters"]:
        if len(request.headers.getlist(str(parameter["name"]))) > 1:
            raise HTTPException(400, detail={"code": "ambiguous_caller_context"})
    return require_workbench_caller_context(
        actor_id=request.headers.get("X-Actor-Id"),
        tenant_id=request.headers.get("X-Tenant-Id"),
        region=request.headers.get("X-Region"),
        caller_application=request.headers.get("X-Caller-Application"),
        booking_center_code=request.headers.get("X-Booking-Center-Code"),
        role=request.headers.get("X-Role"),
    )


PerformanceCallerContext = Annotated[dict[str, str], Depends(require_performance_caller_context)]

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
