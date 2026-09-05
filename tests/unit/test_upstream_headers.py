from app.clients.upstream_headers import (
    build_archive_caller_headers,
    build_idempotent_upstream_headers,
    build_upstream_headers,
)


def test_build_upstream_headers_adds_correlation_and_extras_without_mutating_inputs() -> None:
    extras = {"X-Test": "value"}

    headers = build_upstream_headers("corr-headers", extras=extras)

    assert headers["X-Correlation-Id"] == "corr-headers"
    assert headers["X-Request-Id"].startswith("req_")
    assert headers["X-Trace-Id"]
    assert headers["traceparent"].startswith("00-")
    assert headers["X-Test"] == "value"
    assert extras == {"X-Test": "value"}


def test_build_idempotent_upstream_headers_preserves_reporting_merge_order() -> None:
    caller_headers = {
        "X-Actor-Id": "advisor-123",
        "Idempotency-Key": "caller-overrides-existing-reporting-behavior",
    }

    headers = build_idempotent_upstream_headers(
        "corr-report",
        "generated-idempotency-key",
        caller_headers=caller_headers,
    )

    assert headers["X-Correlation-Id"] == "corr-report"
    assert headers["X-Actor-Id"] == "advisor-123"
    assert headers["Idempotency-Key"] == "caller-overrides-existing-reporting-behavior"


def test_build_idempotent_upstream_headers_supports_service_specific_header_name() -> None:
    headers = build_idempotent_upstream_headers(
        "corr-core-ingestion",
        "idem-core-1",
        idempotency_header="X-Idempotency-Key",
    )

    assert headers["X-Correlation-Id"] == "corr-core-ingestion"
    assert headers["X-Idempotency-Key"] == "idem-core-1"
    assert "Idempotency-Key" not in headers


def test_build_archive_caller_headers_maps_gateway_archive_context() -> None:
    headers = build_archive_caller_headers(
        correlation_id="corr-archive",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-private-bank",
            "X-Region": "SG",
            "X-Role": "relationship-manager",
            "X-Booking-Center-Code": "SG",
        },
    )

    assert headers["X-Correlation-Id"] == "corr-archive"
    assert headers["X-Request-Id"].startswith("req_")
    assert headers["X-Trace-Id"]
    assert headers["traceparent"].startswith("00-")
    assert headers["X-Caller-Service"] == "lotus-gateway"
    assert headers["X-Actor-Type"] == "relationship-manager"
    assert headers["X-Actor-Id"] == "advisor-123"
    assert headers["X-Tenant-Id"] == "tenant-private-bank"
    assert headers["X-Region"] == "SG"
    assert headers["X-Booking-Center-Code"] == "SG"


def test_build_archive_caller_headers_defaults_actor_type() -> None:
    headers = build_archive_caller_headers(
        correlation_id="corr-archive",
        caller_headers={
            "X-Actor-Id": "advisor-123",
            "X-Tenant-Id": "tenant-private-bank",
            "X-Region": "SG",
        },
    )

    assert headers["X-Actor-Type"] == "user"
    assert "X-Booking-Center-Code" not in headers


def test_build_upstream_headers_propagates_the_caller_presented_identity() -> None:
    from starlette.datastructures import Headers

    from app.middleware.caller_identity import (
        capture_caller_identity,
        release_caller_identity,
    )

    token = capture_caller_identity(
        Headers(
            {
                "X-Tenant-Id": "tenant-sg",
                "X-Actor-Id": "PM_SG_001",
                "X-Caller-Application": "lotus-workbench",
                "X-Region": "APAC",
                "X-Booking-Center-Code": "Singapore",
                "X-Role": "ADVISOR",
                # Never propagated ambiently: credentials and entitlement claims.
                "Authorization": "Bearer secret",
                "X-Caller-Capabilities": "advisor.book.read",
                "X-Authorized-Advisor-Id": "PM_SG_001",
            }
        )
    )
    try:
        headers = build_upstream_headers("corr-identity")
    finally:
        release_caller_identity(token)

    assert headers["X-Tenant-Id"] == "tenant-sg"
    assert headers["X-Actor-Id"] == "PM_SG_001"
    assert headers["X-Caller-Application"] == "lotus-workbench"
    assert headers["X-Region"] == "APAC"
    assert headers["X-Booking-Center-Code"] == "Singapore"
    assert headers["X-Role"] == "ADVISOR"
    assert "Authorization" not in headers
    assert "X-Caller-Capabilities" not in headers
    assert "X-Authorized-Advisor-Id" not in headers


def test_explicitly_admitted_caller_headers_win_over_the_ambient_identity() -> None:
    from starlette.datastructures import Headers

    from app.middleware.caller_identity import (
        capture_caller_identity,
        release_caller_identity,
    )

    token = capture_caller_identity(Headers({"X-Tenant-Id": "tenant-presented"}))
    try:
        headers = build_upstream_headers(
            "corr-override",
            caller_headers={"X-Tenant-Id": "tenant-admitted"},
        )
    finally:
        release_caller_identity(token)

    assert headers["X-Tenant-Id"] == "tenant-admitted"


def test_a_request_that_presented_no_identity_propagates_none() -> None:
    headers = build_upstream_headers("corr-anonymous")

    assert "X-Tenant-Id" not in headers
    assert "X-Actor-Id" not in headers
