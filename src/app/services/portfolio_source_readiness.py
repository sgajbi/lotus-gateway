from typing import Any

from app.contracts.portfolio_workflow import (
    PortfolioReadinessBucket,
    PortfolioReadinessIndicator,
    PortfolioReadinessReason,
    PortfolioSupportabilitySummary,
)


def parse_readiness_bucket(payload: Any) -> PortfolioReadinessBucket | None:
    if not isinstance(payload, dict):
        return None
    status_value = optional_text(payload.get("status"))
    if status_value is None:
        return None
    return PortfolioReadinessBucket(
        status=map_source_readiness_status(status_value),
        reasons=parse_readiness_reasons(payload.get("reasons")),
    )


def parse_readiness_reasons(payload: Any) -> list[PortfolioReadinessReason]:
    if not isinstance(payload, list):
        return []
    reasons: list[PortfolioReadinessReason] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        code = optional_text(item.get("code"))
        if code is None:
            continue
        reasons.append(
            PortfolioReadinessReason(
                code=code,
                detail=optional_text(item.get("detail")),
            )
        )
    return reasons


def parse_portfolio_supportability(payload: Any) -> PortfolioSupportabilitySummary | None:
    if not isinstance(payload, dict):
        return None
    state = optional_text(payload.get("state"))
    reason = optional_text(payload.get("reason"))
    if state is None or reason is None:
        return None
    return PortfolioSupportabilitySummary(
        feature_key=(
            optional_text(payload.get("feature_key"))
            or "core.observability.portfolio_supportability"
        ),
        state=state,
        reason=reason,
        freshness_bucket=map_portfolio_supportability_freshness(payload.get("freshness_bucket")),
        ready_domains=optional_int(payload.get("ready_domains")) or 0,
        pending_domains=optional_int(payload.get("pending_domains")) or 0,
        blocked_domains=optional_int(payload.get("blocked_domains")) or 0,
        no_activity_domains=optional_int(payload.get("no_activity_domains")) or 0,
    )


def build_source_readiness_indicators(
    payload: dict[str, Any] | None, detailed_view: bool
) -> list[PortfolioReadinessIndicator]:
    if payload is None:
        return []
    return [
        PortfolioReadinessIndicator(
            key="holdings",
            label="Holdings",
            status=map_source_readiness_status(payload.get("holdings", {}).get("status")),
            href="#portfolio-drilldown" if detailed_view else "#portfolio-insights",
        ),
        PortfolioReadinessIndicator(
            key="pricing",
            label="Pricing",
            status=map_source_readiness_status(payload.get("pricing", {}).get("status")),
            href="#portfolio-attention",
        ),
        PortfolioReadinessIndicator(
            key="transactions",
            label="Transactions",
            status=map_source_readiness_status(payload.get("transactions", {}).get("status")),
            href="#portfolio-drilldown" if detailed_view else "#portfolio-insights",
        ),
        PortfolioReadinessIndicator(
            key="reporting",
            label="Reporting",
            status=map_source_readiness_status(payload.get("reporting", {}).get("status")),
            href="#portfolio-health",
        ),
    ]


def map_source_readiness_status(status_value: Any) -> str:
    normalized = str(status_value or "").strip().upper()
    mapping = {
        "READY": "Ready",
        "PENDING": "Pending",
        "BLOCKED": "Blocked",
        "FAILED": "Blocked",
        "EMPTY": "Empty",
    }
    return mapping.get(normalized, "Pending" if normalized else "Unknown")


def map_portfolio_supportability_freshness(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"fresh", "current"}:
        return "fresh"
    if normalized == "stale":
        return "stale"
    return "unknown"


def optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
