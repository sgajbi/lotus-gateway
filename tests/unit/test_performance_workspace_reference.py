from app.services.performance_workspace_reference import (
    analytics_reference_cache_key,
    resolve_performance_report_end_date,
)


def test_analytics_reference_cache_key_is_stable() -> None:
    assert analytics_reference_cache_key(
        portfolio_id="DEMO_ADV_USD_001",
        as_of_date="2026-03-27",
    ) == ("analytics_reference", "DEMO_ADV_USD_001", "2026-03-27")


def test_resolve_performance_report_end_date_uses_upstream_reference_date() -> None:
    warnings: list[str] = []
    partial_failures = []

    report_end_date = resolve_performance_report_end_date(
        result=(200, {"performance_end_date": "2026-03-26"}),
        fallback_as_of_date="2026-03-27",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert report_end_date == "2026-03-26"
    assert warnings == []
    assert partial_failures == []


def test_resolve_performance_report_end_date_falls_back_for_http_failure() -> None:
    warnings: list[str] = []
    partial_failures = []

    report_end_date = resolve_performance_report_end_date(
        result=(
            503,
            {
                "detail": {
                    "code": "REFERENCE_UNAVAILABLE",
                    "message": "analytics reference unavailable",
                    "debug_payload": {
                        "client_name": "Private Client",
                        "token": "secret-token",
                    },
                }
            },
        ),
        fallback_as_of_date="2026-03-27",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert report_end_date == "2026-03-27"
    assert warnings == ["PERFORMANCE_REFERENCE_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-core"
    assert partial_failures[0].error_code == "HTTP_503"
    assert partial_failures[0].detail == "REFERENCE_UNAVAILABLE: analytics reference unavailable"
    assert "Private Client" not in str(partial_failures[0])
    assert "secret-token" not in str(partial_failures[0])


def test_resolve_performance_report_end_date_falls_back_for_missing_date() -> None:
    warnings: list[str] = []
    partial_failures = []

    report_end_date = resolve_performance_report_end_date(
        result=(200, {"performance_end_date": ""}),
        fallback_as_of_date="2026-03-27",
        warnings=warnings,
        partial_failures=partial_failures,
    )

    assert report_end_date == "2026-03-27"
    assert warnings == ["PERFORMANCE_REFERENCE_MISSING_END_DATE"]
    assert partial_failures == []
