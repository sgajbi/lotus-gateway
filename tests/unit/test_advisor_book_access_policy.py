import pytest

from app.services.advisor_book_access_policy import (
    AdvisorBookCallerContextError,
    require_advisor_book_caller_context,
)


def _headers(**overrides: str | None) -> dict[str, str | None]:
    values: dict[str, str | None] = {
        "actor_id": "advisor_sg_001",
        "caller_application": "lotus-workbench",
        "tenant_id": "tenant-sg",
        "region": "APAC",
        "booking_center_code": "Singapore",
        "role": "ADVISOR",
        "capabilities": "portfolio.read,advisor.book.read",
    }
    values.update(overrides)
    return values


def test_advisor_book_context_derives_manager_identity_from_trusted_actor() -> None:
    context = require_advisor_book_caller_context(**_headers())

    assert context.portfolio_manager_id == "advisor_sg_001"
    assert context.tenant_id == "tenant-sg"
    assert context.booking_center_code == "Singapore"
    assert context.role == "ADVISOR"
    assert context.caller_application == "lotus-workbench"


@pytest.mark.parametrize(
    "missing_field",
    [
        "actor_id",
        "tenant_id",
        "region",
        "booking_center_code",
        "role",
        "capabilities",
    ],
)
def test_advisor_book_context_fails_closed_when_required_context_is_missing(
    missing_field: str,
) -> None:
    with pytest.raises(AdvisorBookCallerContextError) as exc_info:
        require_advisor_book_caller_context(**_headers(**{missing_field: None}))

    assert exc_info.value.code == "advisor_book_caller_context_missing"
    assert exc_info.value.status_code == 400


@pytest.mark.parametrize("role", ["CLIENT", "OPERATIONS", "SUPERVISOR", "advisor"])
def test_advisor_book_context_rejects_unimplemented_roles(role: str) -> None:
    with pytest.raises(AdvisorBookCallerContextError) as exc_info:
        require_advisor_book_caller_context(**_headers(role=role))

    assert exc_info.value.code == "advisor_book_access_denied"
    assert exc_info.value.status_code == 403


@pytest.mark.parametrize(
    "capabilities",
    [
        "portfolio.read",
        "advisor.book.read.all",
        "Advisor.Book.Read",
        "advisor_book_read",
    ],
)
def test_advisor_book_context_requires_exact_read_capability(capabilities: str) -> None:
    with pytest.raises(AdvisorBookCallerContextError) as exc_info:
        require_advisor_book_caller_context(**_headers(capabilities=capabilities))

    assert exc_info.value.code == "advisor_book_access_denied"


@pytest.mark.parametrize(
    "actor_id",
    ["../advisor", "advisor/other", "", "a" * 129],
)
def test_advisor_book_context_rejects_unsafe_actor_identity(actor_id: str) -> None:
    expected_code = (
        "advisor_book_caller_context_missing"
        if not actor_id.strip()
        else "advisor_book_caller_context_invalid"
    )
    with pytest.raises(AdvisorBookCallerContextError) as exc_info:
        require_advisor_book_caller_context(**_headers(actor_id=actor_id))

    assert exc_info.value.code == expected_code


def test_advisor_book_context_defaults_the_internal_caller_application() -> None:
    context = require_advisor_book_caller_context(**_headers(caller_application=" "))

    assert context.caller_application == "lotus-gateway"
