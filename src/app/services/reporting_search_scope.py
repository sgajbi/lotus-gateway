"""Admitted-scope fencing for the report-job search boundary.

A search filter may only narrow within the caller's admitted scope, never
enlarge it. The effective tenant and region fences ARE the admitted
X-Tenant-Id / X-Region: a conflicting supplied filter is refused before any
source call, the fence is always sent to the source, and the source's
applied-filter echo plus every returned row is validated against the fence
before success is published. A cross-tenant or cross-region support read
would need its own explicitly authorized contract; a query string is not
authorization.
"""

from typing import Any

from fastapi import HTTPException, status

from app.contracts.reporting_query import ReportJobListResponse

_SCOPE_AXES: tuple[tuple[str, str, str], ...] = (
    ("tenantId", "X-Tenant-Id", "tenant"),
    ("region", "X-Region", "region"),
)


def resolve_search_scope_params(
    *,
    caller_headers: dict[str, str],
    query_params: dict[str, Any],
) -> dict[str, Any]:
    """Return the search params with the admitted fence applied, refusing conflicts."""

    fenced = dict(query_params)
    for param_name, header_name, axis in _SCOPE_AXES:
        admitted = (caller_headers.get(header_name) or "").strip()
        supplied = str(fenced.get(param_name) or "").strip()
        if supplied and admitted and supplied != admitted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": f"report_job_{axis}_scope_ambiguous",
                    "message": (
                        f"The {param_name} filter disagrees with the admitted caller "
                        f"{axis} scope; a search filter cannot enlarge admitted scope."
                    ),
                },
            )
        if admitted:
            fenced[param_name] = admitted
    return fenced


def assert_search_result_within_scope(
    response: ReportJobListResponse,
    *,
    caller_headers: dict[str, str],
) -> None:
    """Refuse a source result whose echo or rows leave the admitted fence."""

    for _, header_name, axis in _SCOPE_AXES:
        admitted = (caller_headers.get(header_name) or "").strip()
        if not admitted:
            continue
        applied = getattr(response.applied_filters, "tenant_id" if axis == "tenant" else axis)
        if (applied or "").strip() != admitted:
            _raise_scope_violation(axis, "applied-filter echo")
        row_field = "tenant_id" if axis == "tenant" else axis
        for item in response.items:
            if (getattr(item, row_field, "") or "").strip() != admitted:
                _raise_scope_violation(axis, "returned row")


def _raise_scope_violation(axis: str, evidence: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "code": "report_job_source_scope_violation",
            "message": (
                f"lotus-report returned a job search whose {evidence} is outside the "
                f"admitted {axis} scope; the result is refused rather than published."
            ),
        },
    )
