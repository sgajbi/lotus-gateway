from app.services.portfolio_source_readiness import (
    build_source_readiness_indicators,
    map_portfolio_supportability_freshness,
    map_source_readiness_status,
    parse_portfolio_supportability,
    parse_readiness_bucket,
    parse_readiness_reasons,
)


def test_parse_readiness_bucket_maps_status_and_reasons() -> None:
    bucket = parse_readiness_bucket(
        {
            "status": "FAILED",
            "reasons": [
                {"code": "NO_PRICE", "detail": "latest price unavailable"},
                {"detail": "missing code"},
                "not-a-reason",
            ],
        }
    )

    assert bucket is not None
    assert bucket.status == "Blocked"
    assert len(bucket.reasons) == 1
    assert bucket.reasons[0].code == "NO_PRICE"
    assert bucket.reasons[0].detail == "latest price unavailable"


def test_parse_readiness_bucket_requires_object_and_status() -> None:
    assert parse_readiness_bucket(None) is None
    assert parse_readiness_bucket({"reasons": []}) is None


def test_parse_readiness_reasons_ignores_non_list_payload() -> None:
    assert parse_readiness_reasons({"code": "NO_PRICE"}) == []


def test_parse_portfolio_supportability_defaults_feature_and_counts() -> None:
    supportability = parse_portfolio_supportability(
        {
            "state": "ready",
            "reason": "all_domains_ready",
            "freshness_bucket": "current",
            "ready_domains": "3",
            "pending_domains": None,
            "blocked_domains": "bad-count",
            "no_activity_domains": 1,
        }
    )

    assert supportability is not None
    assert supportability.feature_key == "core.observability.portfolio_supportability"
    assert supportability.state == "ready"
    assert supportability.reason == "all_domains_ready"
    assert supportability.freshness_bucket == "fresh"
    assert supportability.ready_domains == 3
    assert supportability.pending_domains == 0
    assert supportability.blocked_domains == 0
    assert supportability.no_activity_domains == 1


def test_parse_portfolio_supportability_requires_state_and_reason() -> None:
    assert parse_portfolio_supportability([]) is None
    assert parse_portfolio_supportability({"state": "ready"}) is None
    assert parse_portfolio_supportability({"reason": "missing_state"}) is None


def test_build_source_readiness_indicators_maps_detail_mode_links() -> None:
    indicators = build_source_readiness_indicators(
        {
            "holdings": {"status": "READY"},
            "pricing": {"status": "EMPTY"},
            "transactions": {"status": "pending"},
            "reporting": {"status": "blocked"},
        },
        detailed_view=True,
    )

    assert [indicator.key for indicator in indicators] == [
        "holdings",
        "pricing",
        "transactions",
        "reporting",
    ]
    assert [indicator.status for indicator in indicators] == [
        "Ready",
        "Empty",
        "Pending",
        "Blocked",
    ]
    assert indicators[0].href == "#portfolio-drilldown"
    assert indicators[2].href == "#portfolio-drilldown"


def test_build_source_readiness_indicators_maps_summary_mode_links() -> None:
    indicators = build_source_readiness_indicators(
        {"holdings": {"status": "READY"}, "transactions": {"status": "READY"}},
        detailed_view=False,
    )

    assert indicators[0].href == "#portfolio-insights"
    assert indicators[2].href == "#portfolio-insights"
    assert indicators[1].status == "Unknown"
    assert indicators[3].status == "Unknown"


def test_build_source_readiness_indicators_requires_payload() -> None:
    assert build_source_readiness_indicators(None, detailed_view=False) == []


def test_map_source_readiness_status_defaults_are_stable() -> None:
    assert map_source_readiness_status("READY") == "Ready"
    assert map_source_readiness_status("FAILED") == "Blocked"
    assert map_source_readiness_status("unexpected") == "Pending"
    assert map_source_readiness_status(None) == "Unknown"


def test_map_portfolio_supportability_freshness_defaults_are_stable() -> None:
    assert map_portfolio_supportability_freshness("fresh") == "fresh"
    assert map_portfolio_supportability_freshness("current") == "fresh"
    assert map_portfolio_supportability_freshness("stale") == "stale"
    assert map_portfolio_supportability_freshness("unknown-value") == "unknown"
