import pytest

from app.services.advisor_cockpit_access_policy import (
    ADVISOR_COCKPIT_ACKNOWLEDGE_CAPABILITY,
    ADVISOR_COCKPIT_READ_CAPABILITY,
    AdvisorCockpitAccessError,
    require_advisor_cockpit_caller_context,
    require_advisor_cockpit_capability,
    require_advisor_cockpit_portfolio_scope,
)


def _context(**overrides: str | None):
    values: dict[str, str | None] = {
        "actor_id": "advisor_sg_001",
        "caller_application": "lotus-workbench",
        "tenant_id": "tenant-sg",
        "region": "APAC",
        "booking_center_code": "SG",
        "legal_entity_code": "SGPB",
        "role": "ADVISOR",
        "capabilities": (
            "advisory.advisor_cockpit.read,advisory.advisor_cockpit.acknowledge"
        ),
        "principal_status": "ACTIVE",
        "authorized_advisor_id": "advisor_sg_001",
        "authorized_portfolio_id": "PB_SG_GLOBAL_BAL_001",
    }
    values.update(overrides)
    return require_advisor_cockpit_caller_context(**values)


def test_caller_context_preserves_bounded_trusted_authority() -> None:
    caller = _context()

    assert caller.actor_id == "advisor_sg_001"
    assert caller.role == "ADVISOR"
    assert caller.capabilities == frozenset(
        {ADVISOR_COCKPIT_READ_CAPABILITY, ADVISOR_COCKPIT_ACKNOWLEDGE_CAPABILITY}
    )
    assert caller.authorized_advisor_id == "advisor_sg_001"
    assert caller.authorized_portfolio_id == "PB_SG_GLOBAL_BAL_001"
    assert caller.upstream_headers() == {
        "X-Actor-Id": "advisor_sg_001",
        "X-Role": "ADVISOR",
        "X-Tenant-Id": "tenant-sg",
        "X-Legal-Entity-Code": "SGPB",
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": (
            "advisory.advisor_cockpit.acknowledge,advisory.advisor_cockpit.read"
        ),
        "X-Principal-Status": "ACTIVE",
        "X-Authorized-Advisor-Id": "advisor_sg_001",
        "X-Authorized-Portfolio-Id": "PB_SG_GLOBAL_BAL_001",
    }


@pytest.mark.parametrize(
    "field",
    [
        "actor_id",
        "caller_application",
        "tenant_id",
        "region",
        "booking_center_code",
        "legal_entity_code",
        "role",
        "capabilities",
        "principal_status",
    ],
)
def test_caller_context_rejects_missing_authority_fields(field: str) -> None:
    with pytest.raises(AdvisorCockpitAccessError) as exc:
        _context(**{field: None})

    assert exc.value.code == "advisor_cockpit_caller_context_missing"
    assert exc.value.status_code == 400


@pytest.mark.parametrize(
    ("overrides", "expected_code", "expected_status"),
    [
        ({"actor_id": "../../advisor"}, "advisor_cockpit_caller_context_invalid", 400),
        (
            {"authorized_portfolio_id": "../../portfolio"},
            "advisor_cockpit_caller_context_invalid",
            400,
        ),
        ({"role": "RELATIONSHIP_MANAGER"}, "advisor_cockpit_access_denied", 403),
        (
            {"authorized_advisor_id": "advisor_sg_999"},
            "advisor_cockpit_access_denied",
            403,
        ),
        ({"principal_status": "LOCKED"}, "advisor_cockpit_principal_invalid", 401),
    ],
)
def test_caller_context_rejects_malformed_or_unsupported_authority(
    overrides: dict[str, str],
    expected_code: str,
    expected_status: int,
) -> None:
    with pytest.raises(AdvisorCockpitAccessError) as exc:
        _context(**overrides)

    assert exc.value.code == expected_code
    assert exc.value.status_code == expected_status


def test_capability_and_portfolio_checks_fail_closed() -> None:
    caller = _context()

    require_advisor_cockpit_capability(caller, ADVISOR_COCKPIT_READ_CAPABILITY)
    assert (
        require_advisor_cockpit_portfolio_scope(caller, "PB_SG_GLOBAL_BAL_001")
        == "PB_SG_GLOBAL_BAL_001"
    )

    with pytest.raises(AdvisorCockpitAccessError) as capability_error:
        require_advisor_cockpit_capability(caller, "advisory.advisor_cockpit.admin")
    with pytest.raises(AdvisorCockpitAccessError) as portfolio_error:
        require_advisor_cockpit_portfolio_scope(caller, "PB_NOT_ENTITLED")

    assert capability_error.value.code == "advisor_cockpit_access_denied"
    assert portfolio_error.value.code == "advisor_cockpit_portfolio_access_denied"


def test_requested_portfolio_requires_explicit_entitlement() -> None:
    caller = _context(authorized_portfolio_id=None)

    with pytest.raises(AdvisorCockpitAccessError) as exc:
        require_advisor_cockpit_portfolio_scope(caller, "PB_SG_GLOBAL_BAL_001")

    assert exc.value.code == "advisor_cockpit_portfolio_scope_required"
    assert exc.value.status_code == 401


def test_advisor_scope_is_derived_from_the_authenticated_actor() -> None:
    caller = _context(authorized_advisor_id=None)

    assert caller.authorized_advisor_id == caller.actor_id
    assert caller.upstream_headers()["X-Authorized-Advisor-Id"] == caller.actor_id
