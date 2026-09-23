import pytest
from fastapi import HTTPException

from app.services.advisory_copilot_access_policy import (
    COPILOT_ACTION_RUN,
    COPILOT_PROPOSAL_RUNS_READ,
    COPILOT_RESOURCE_READ,
    COPILOT_REVIEW,
    require_advisory_copilot_caller_context,
)

ADVISORY_COPILOT_REVIEW_CAPABILITY = COPILOT_REVIEW.capability


def _headers(**overrides: str | None) -> dict[str, str | None]:
    values: dict[str, str | None] = {
        "actor_id": "desk_head_sg_001",
        "tenant_id": "tenant-sg-001",
        "legal_entity_code": "pb_sg",
        "role": "advisory_supervisor",
        "capabilities": ADVISORY_COPILOT_REVIEW_CAPABILITY,
        "principal_status": "active",
        "authorized_proposal_id": "pp_740969c87c00",
        "authorized_portfolio_id": "PB_SG_GLOBAL_BAL_001",
    }
    values.update(overrides)
    return values


def test_review_context_maps_workbench_headers_to_advise_principal_contract() -> None:
    context = require_advisory_copilot_caller_context(operation=COPILOT_REVIEW, **_headers())

    assert context.upstream_headers() == {
        "X-Actor-Id": "desk_head_sg_001",
        "X-Role": "ADVISORY_SUPERVISOR",
        "X-Tenant-Id": "tenant-sg-001",
        "X-Legal-Entity-Code": "PB_SG",
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": ADVISORY_COPILOT_REVIEW_CAPABILITY,
        "X-Principal-Status": "ACTIVE",
        "X-Authorized-Proposal-Id": "pp_740969c87c00",
        "X-Authorized-Portfolio-Id": "PB_SG_GLOBAL_BAL_001",
    }


def test_tenant_scoped_read_can_resolve_resource_scope_without_inventing_it() -> None:
    context = require_advisory_copilot_caller_context(
        operation=COPILOT_RESOURCE_READ,
        **_headers(
            capabilities=COPILOT_RESOURCE_READ.capability,
            authorized_proposal_id=None,
            authorized_portfolio_id=None,
        ),
    )

    assert context.upstream_headers() == {
        "X-Actor-Id": "desk_head_sg_001",
        "X-Role": "ADVISORY_SUPERVISOR",
        "X-Tenant-Id": "tenant-sg-001",
        "X-Legal-Entity-Code": "PB_SG",
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": COPILOT_RESOURCE_READ.capability,
        "X-Principal-Status": "ACTIVE",
    }


def test_proposal_run_read_requires_proposal_but_not_unresolved_portfolio() -> None:
    context = require_advisory_copilot_caller_context(
        operation=COPILOT_PROPOSAL_RUNS_READ,
        **_headers(
            capabilities=COPILOT_PROPOSAL_RUNS_READ.capability,
            authorized_portfolio_id=None,
        ),
    )

    assert context.authorized_proposal_id == "pp_740969c87c00"
    assert context.authorized_portfolio_id is None


def test_mutation_still_refuses_missing_portfolio_scope() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_advisory_copilot_caller_context(
            operation=COPILOT_ACTION_RUN,
            **_headers(
                role="ADVISOR",
                capabilities=COPILOT_ACTION_RUN.capability,
                authorized_proposal_id=None,
                authorized_portfolio_id=None,
            ),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == {
        "code": "advisory_copilot_scope_required",
        "message": "Advisory Copilot requires trusted resource scope.",
        "missing_headers": ["X-Authorized-Portfolio-Id"],
    }


@pytest.mark.parametrize(
    ("overrides", "code", "status_code"),
    [
        ({"actor_id": None}, "advisory_copilot_review_caller_context_missing", 400),
        ({"principal_status": "locked"}, "advisory_copilot_review_principal_invalid", 401),
        ({"role": "ADVISOR"}, "advisory_copilot_review_access_denied", 403),
        ({"capabilities": "portfolio.read"}, "advisory_copilot_review_capability_required", 403),
        (
            {"authorized_proposal_id": None},
            "advisory_copilot_review_scope_required",
            403,
        ),
        (
            {"authorized_portfolio_id": None},
            "advisory_copilot_review_scope_required",
            403,
        ),
        ({"actor_id": "../../desk"}, "advisory_copilot_review_caller_context_invalid", 400),
        (
            {"authorized_proposal_id": "../../proposal"},
            "advisory_copilot_review_caller_context_invalid",
            400,
        ),
    ],
)
def test_review_context_fails_closed_for_untrusted_or_unentitled_headers(
    overrides: dict[str, str | None],
    code: str,
    status_code: int,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_advisory_copilot_caller_context(operation=COPILOT_REVIEW, **_headers(**overrides))

    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail["code"] == code
