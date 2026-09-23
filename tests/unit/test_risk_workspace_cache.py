from dataclasses import replace

from app.contracts.risk_workspace import (
    WorkbenchRiskMetadata,
    WorkbenchRiskSummaryResponse,
)
from app.services.risk_workspace_cache import (
    attribution_cache_key,
    concentration_cache_key,
    drawdown_cache_key,
    rolling_cache_key,
    summary_cache_key,
    with_cache_status,
)
from app.services.risk_workspace_requests import (
    build_attribution_request_context,
    build_concentration_request_context,
    build_drawdown_request_context,
    build_rolling_request_context,
    build_summary_request_context,
)


def test_summary_cache_key_uses_request_shape_without_correlation_id() -> None:
    first = build_summary_request_context(
        portfolio_id="PF_1",
        correlation_id="corr-1",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        report_start_date=None,
        report_end_date="2026-04-10",
        reporting_currency="USD",
        tenant_id="tenant-sg",
    )
    second = build_summary_request_context(
        portfolio_id="PF_1",
        correlation_id="corr-2",
        period="YTD",
        detail_basis="NET",
        benchmark_code="BMK_1",
        as_of_date="2026-04-04",
        report_start_date=None,
        report_end_date="2026-04-10",
        reporting_currency="USD",
        tenant_id="tenant-sg",
    )

    assert summary_cache_key(first) == summary_cache_key(second)
    assert "corr-1" not in summary_cache_key(first)
    assert "corr-2" not in summary_cache_key(second)


def test_risk_cache_keys_keep_omitted_and_blank_window_identity_distinct() -> None:
    common = {
        "portfolio_id": "PF_1",
        "correlation_id": "corr-1",
        "period": "EXPLICIT",
        "benchmark_code": "BMK_1",
        "as_of_date": "2026-04-10",
        "report_start_date": None,
        "report_end_date": "2026-04-10",
        "reporting_currency": "USD",
    }
    keyed_contexts = [
        (
            summary_cache_key,
            build_summary_request_context(
                **common,
                detail_basis="NET",
                tenant_id="tenant-sg",
            ),
        ),
        (
            concentration_cache_key,
            build_concentration_request_context(
                **common,
                tenant_id="tenant-sg",
            ),
        ),
        (
            drawdown_cache_key,
            build_drawdown_request_context(
                **common,
                detail_basis="NET",
                include_underwater_series=False,
            ),
        ),
        (
            rolling_cache_key,
            build_rolling_request_context(
                **common,
                detail_basis="NET",
                include_time_series=False,
            ),
        ),
        (
            attribution_cache_key,
            build_attribution_request_context(
                **common,
                detail_basis="NET",
                attribution_type="TOTAL_RISK",
                grouping_dimension="SECTOR",
            ),
        ),
    ]

    for cache_key, context in keyed_contexts:
        assert cache_key(context) != cache_key(replace(context, report_start_date=""))
        assert cache_key(context) != cache_key(replace(context, report_end_date=""))


def test_with_cache_status_updates_correlation_without_mutating_cached_response() -> None:
    cached = WorkbenchRiskSummaryResponse(
        correlation_id="corr-original",
        portfolio_id="PF_1",
        period="YTD",
        detail_basis="NET",
        as_of_date="2026-04-04",
        benchmark_code="BMK_1",
        state="ready",
        payload=None,
        metadata=WorkbenchRiskMetadata(
            generated_at="2026-04-04T00:00:00Z",
            cache_status="miss",
        ),
    )

    response = with_cache_status(cached, correlation_id="corr-replay", cache_hit=True)

    assert response.correlation_id == "corr-replay"
    assert response.metadata.cache_status == "hit"
    assert cached.correlation_id == "corr-original"
    assert cached.metadata.cache_status == "miss"
