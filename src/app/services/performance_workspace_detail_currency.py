DETAIL_CURRENCY_BASE_FALLBACK_WARNING = "PERFORMANCE_DETAILS_CURRENCY_NOT_APPLIED_BASE"
DETAIL_CURRENCY_REJECTION_WARNING = "PERFORMANCE_DETAILS_CURRENCY_REJECTED"

# lotus-performance cannot currently source FX for stateful detail requests. Keep this decision
# explicit so the source-owned capability can be re-enabled at one seam after #470 is complete.
DETAIL_CURRENCY_FORWARDING_ENABLED = False


def resolve_detail_currency_request(
    *,
    requested_currency: str | None,
    base_currency: str,
) -> str | None:
    """Return the currency override safe for stateful detail requests."""
    if not requested_currency or requested_currency == base_currency:
        return None
    if not DETAIL_CURRENCY_FORWARDING_ENABLED:
        return None
    return requested_currency


def detail_currency_fallback_applies(
    *,
    requested_currency: str | None,
    base_currency: str,
    upstream_currency: str | None,
) -> bool:
    return (
        requested_currency is not None
        and requested_currency != base_currency
        and upstream_currency is None
    )
