import pytest
from fastapi import HTTPException

from app.services.portfolio_upstream_payloads import (
    optional_payload,
    raise_on_upstream_client_error,
    require_payload,
)


def test_require_payload_returns_success_payload() -> None:
    payload = {"portfolio_id": "PB_TEST_001"}

    assert require_payload((200, payload), "lotus-core portfolio unavailable") == payload


def test_require_payload_raises_product_safe_gateway_error() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_payload(
            (503, {"detail": {"portfolio_id": "PB_SENSITIVE", "traceback": "raw"}}),
            "lotus-core portfolio unavailable",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "lotus-core portfolio unavailable: upstream request failed"


def test_raise_on_upstream_client_error_preserves_client_status_with_safe_detail() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_on_upstream_client_error(
            (404, {"message": "portfolio not found"}),
            detail_prefix="lotus-core readiness unavailable",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "lotus-core readiness unavailable: portfolio not found"


def test_optional_payload_records_partial_failure_for_unavailable_source() -> None:
    warnings: list[str] = []
    partial_failures = []

    assert (
        optional_payload(
            (500, {"detail": "readiness unavailable"}),
            "lotus-core",
            "PORTFOLIO_SOURCE_READINESS_UNAVAILABLE",
            warnings,
            partial_failures,
        )
        is None
    )

    assert warnings == ["PORTFOLIO_SOURCE_READINESS_UNAVAILABLE"]
    assert len(partial_failures) == 1
    assert partial_failures[0].source_service == "lotus-core"
    assert partial_failures[0].error_code == "PORTFOLIO_SOURCE_READINESS_UNAVAILABLE"
    assert partial_failures[0].detail == "readiness unavailable"
