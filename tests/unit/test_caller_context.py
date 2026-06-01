import pytest
from fastapi import HTTPException

from app.services.caller_context import caller_context_headers


def test_caller_context_headers_strips_and_defaults_optional_values() -> None:
    headers = caller_context_headers(
        actor_id=" advisor-1 ",
        caller_application=" ",
        tenant_id=" tenant-sg ",
        region=" APAC ",
        booking_center_code=" SGPB ",
        role=" advisor ",
    )

    assert headers == {
        "X-Actor-Id": "advisor-1",
        "X-Caller-Application": "lotus-gateway",
        "X-Tenant-Id": "tenant-sg",
        "X-Region": "APAC",
        "X-Booking-Center-Code": "SGPB",
        "X-Role": "advisor",
    }


def test_caller_context_headers_rejects_blank_required_values() -> None:
    with pytest.raises(HTTPException) as exc_info:
        caller_context_headers(
            actor_id=" ",
            caller_application="lotus-workbench",
            tenant_id="tenant-sg",
            region="APAC",
            booking_center_code=None,
            role=None,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["missing_headers"] == ["X-Actor-Id"]
