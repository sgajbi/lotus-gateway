import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.services.dpm_manage_request_authority import (
    DpmManageRequestAuthority,
    DpmManageRequestAuthorityError,
    authorize_dpm_manage_mutation_headers,
    bind_dpm_manage_request_authority,
    build_dpm_manage_request_authority,
    dpm_manage_request_authority_scope,
    forward_dpm_manage_read_headers,
)


def _authority() -> DpmManageRequestAuthority:
    return DpmManageRequestAuthority(
        actor_id="pm_sg_001",
        tenant_id="tenant-sg",
        role="PORTFOLIO_MANAGER",
        region="APAC",
    )


def test_dpm_manage_authority_separates_read_and_write_scope() -> None:
    authority = build_dpm_manage_request_authority(
        actor_id=" pm_sg_001 ",
        tenant_id=" tenant-sg ",
        role=" PORTFOLIO_MANAGER ",
        region=" APAC ",
    )

    assert authority.caller_headers() == {
        "X-Actor-Id": "pm_sg_001",
        "X-Tenant-Id": "tenant-sg",
        "X-Role": "PORTFOLIO_MANAGER",
        "X-Region": "APAC",
    }
    assert authority.mutation_headers() == {
        **authority.caller_headers(),
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": "manage.write",
    }


@pytest.mark.parametrize(
    ("values", "expected_code"),
    [
        (
            {"actor_id": None, "tenant_id": "tenant-sg", "role": "PM", "region": "APAC"},
            "dpm_caller_context_missing",
        ),
        (
            {
                "actor_id": "pm sg 001",
                "tenant_id": "tenant-sg",
                "role": "PM",
                "region": "APAC",
            },
            "dpm_caller_context_invalid",
        ),
    ],
)
def test_dpm_manage_authority_rejects_missing_or_invalid_identity(
    values: dict[str, str | None],
    expected_code: str,
) -> None:
    with pytest.raises(HTTPException) as raised:
        build_dpm_manage_request_authority(**values)

    assert getattr(raised.value, "status_code", None) == 400
    assert raised.value.detail["code"] == expected_code


def test_dpm_manage_read_authority_forwards_only_validated_caller_context() -> None:
    with dpm_manage_request_authority_scope(_authority()):
        headers = forward_dpm_manage_read_headers(
            {
                "X-Correlation-Id": "corr-read-001",
                "X-Actor-Id": "browser-actor",
                "X-Tenant-Id": "other-tenant",
                "X-Role": "ADMIN",
                "X-Service-Identity": "browser-service",
                "X-Capabilities": "manage.admin",
            }
        )

    assert headers == {
        "X-Correlation-Id": "corr-read-001",
        "X-Actor-Id": "pm_sg_001",
        "X-Tenant-Id": "tenant-sg",
        "X-Role": "PORTFOLIO_MANAGER",
        "X-Region": "APAC",
    }


def test_dpm_manage_read_authority_preserves_non_dpm_client_compatibility() -> None:
    headers = {
        "X-Correlation-Id": "corr-unbound-read",
        "X-Tenant-Id": "existing-internal-scope",
    }

    assert forward_dpm_manage_read_headers(headers) == headers


def test_dpm_manage_mutation_authority_replaces_untrusted_workload_headers() -> None:
    with dpm_manage_request_authority_scope(_authority()):
        headers = authorize_dpm_manage_mutation_headers(
            {
                "X-Correlation-Id": "corr-001",
                "Idempotency-Key": "idem-001",
                "X-Actor-Id": "browser-actor",
                "X-Tenant-Id": "other-tenant",
                "X-Role": "ADMIN",
                "X-Service-Identity": "browser-service",
                "X-Capabilities": "manage.admin",
            }
        )

    assert headers == {
        "X-Correlation-Id": "corr-001",
        "Idempotency-Key": "idem-001",
        "X-Actor-Id": "pm_sg_001",
        "X-Tenant-Id": "tenant-sg",
        "X-Role": "PORTFOLIO_MANAGER",
        "X-Region": "APAC",
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": "manage.write",
    }


def test_dpm_manage_mutation_authority_fails_closed_outside_request_scope() -> None:
    with pytest.raises(DpmManageRequestAuthorityError):
        authorize_dpm_manage_mutation_headers({"X-Correlation-Id": "corr-unbound"})


def test_dpm_request_dependency_requires_identity_for_reads_and_mutations() -> None:
    application = FastAPI()

    @application.get("/dpm", dependencies=[Depends(bind_dpm_manage_request_authority)])
    async def read_dpm() -> dict[str, str]:
        return forward_dpm_manage_read_headers({"X-Correlation-Id": "corr-read"})

    @application.post("/dpm", dependencies=[Depends(bind_dpm_manage_request_authority)])
    async def write_dpm() -> dict[str, str]:
        return authorize_dpm_manage_mutation_headers({"X-Correlation-Id": "corr-write"})

    client = TestClient(application)

    for method in (client.get, client.post):
        denied = method("/dpm")
        assert denied.status_code == 400
        assert denied.json()["detail"]["code"] == "dpm_caller_context_missing"

    caller_headers = {
        "X-Actor-Id": "pm_sg_001",
        "X-Tenant-Id": "tenant-sg",
        "X-Role": "PORTFOLIO_MANAGER",
        "X-Region": "APAC",
        "X-Service-Identity": "untrusted-browser",
        "X-Capabilities": "manage.admin",
    }
    accepted_read = client.get("/dpm", headers=caller_headers)
    assert accepted_read.status_code == 200
    assert accepted_read.json()["X-Actor-Id"] == "pm_sg_001"
    assert "X-Service-Identity" not in accepted_read.json()
    assert "X-Capabilities" not in accepted_read.json()

    accepted_write = client.post("/dpm", headers=caller_headers)
    assert accepted_write.status_code == 200
    assert accepted_write.json()["X-Service-Identity"] == "lotus-gateway"
    assert accepted_write.json()["X-Capabilities"] == "manage.write"
    assert accepted_write.json()["X-Actor-Id"] == "pm_sg_001"
