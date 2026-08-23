from fastapi import Query

WORKBENCH_AS_OF_DATE_QUERY = Query(
    default=None,
    pattern=r"^\d{4}-\d{2}-\d{2}$",
    description=(
        "Optional requested review as-of date. It is preserved as requested context; the "
        "response effective date is source-derived and may be unavailable."
    ),
    examples=["2026-08-23"],
)
