import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.services.dpm_manage_mutation_authority import (
    DpmManageMutationAuthority,
    DpmManageMutationAuthorityError,
    authorize_dpm_manage_mutation_headers,
    bind_dpm_manage_mutation_authority,
    build_dpm_manage_mutation_authority,
    dpm_manage_mutation_authority_scope,
)


def _authority() -> DpmManageMutationAuthority:
    return DpmManageMutationAuthority(
        actor_id="pm_sg_001",
        tenant_id="tenant-sg",
        role="PORTFOLIO_MANAGER",
        region="APAC",
    )


def test_dpm_manage_authority_derives_exact_workload_scope() -> None:
    authority = build_dpm_manage_mutation_authority(
        actor_id=" pm_sg_001 ",
        tenant_id=" tenant-sg ",
        role=" PORTFOLIO_MANAGER ",
        region=" APAC ",
    )

    assert authority.upstream_headers() == {
        "X-Actor-Id": "pm_sg_001",
        "X-Tenant-Id": "tenant-sg",
        "X-Role": "PORTFOLIO_MANAGER",
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": "manage.write",
        "X-Region": "APAC",
    }


@pytest.mark.parametrize(
    ("values", "expected_code"),
    [
        (
            {"actor_id": None, "tenant_id": "tenant-sg", "role": "PM", "region": "APAC"},
            "dpm_mutation_caller_context_missing",
        ),
        (
            {
                "actor_id": "pm sg 001",
                "tenant_id": "tenant-sg",
                "role": "PM",
                "region": "APAC",
            },
            "dpm_mutation_caller_context_invalid",
        ),
    ],
)
def test_dpm_manage_authority_rejects_missing_or_invalid_identity(
    values: dict[str, str | None],
    expected_code: str,
) -> None:
    with pytest.raises(HTTPException) as raised:
        build_dpm_manage_mutation_authority(**values)

    assert getattr(raised.value, "status_code", None) == 400
    assert raised.value.detail["code"] == expected_code


def test_dpm_manage_authority_replaces_untrusted_workload_headers() -> None:
    with dpm_manage_mutation_authority_scope(_authority()):
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
        "X-Service-Identity": "lotus-gateway",
        "X-Capabilities": "manage.write",
        "X-Region": "APAC",
    }


def test_dpm_manage_authority_fails_closed_outside_request_scope() -> None:
    with pytest.raises(DpmManageMutationAuthorityError):
        authorize_dpm_manage_mutation_headers({"X-Correlation-Id": "corr-unbound"})


def test_dpm_request_dependency_requires_identity_for_registered_mutations() -> None:
    application = FastAPI()

    @application.get("/dpm")
    async def read_dpm() -> dict[str, str]:
        return {"state": "readable"}

    @application.post("/dpm", dependencies=[Depends(bind_dpm_manage_mutation_authority)])
    async def write_dpm() -> dict[str, str]:
        return authorize_dpm_manage_mutation_headers({"X-Correlation-Id": "corr-http"})

    client = TestClient(application)

    assert client.get("/dpm").json() == {"state": "readable"}
    denied = client.post("/dpm")
    assert denied.status_code == 400
    assert denied.json()["detail"]["code"] == "dpm_mutation_caller_context_missing"

    accepted = client.post(
        "/dpm",
        headers={
            "X-Actor-Id": "pm_sg_001",
            "X-Tenant-Id": "tenant-sg",
            "X-Role": "PORTFOLIO_MANAGER",
            "X-Region": "APAC",
            "X-Service-Identity": "untrusted-browser",
            "X-Capabilities": "manage.admin",
        },
    )
    assert accepted.status_code == 200
    assert accepted.json()["X-Service-Identity"] == "lotus-gateway"
    assert accepted.json()["X-Capabilities"] == "manage.write"
    assert accepted.json()["X-Actor-Id"] == "pm_sg_001"
