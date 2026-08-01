from __future__ import annotations

from app.clients.upstream_headers import build_upstream_headers

MANAGE_WRITE_CAPABILITY = "manage.write"
MANAGE_PM_QUALITY_READ_CAPABILITY = "pm_quality.read"
MANAGE_WRITE_SERVICE_IDENTITY = "lotus-gateway"
MANAGE_WRITE_ACTOR_ID = "lotus-gateway-dpm-command-center"
MANAGE_WRITE_TENANT_ID = "tenant-sg-001"
MANAGE_WRITE_ROLE = "SERVICE"


def build_manage_write_headers(
    correlation_id: str,
    *,
    extras: dict[str, str] | None = None,
) -> dict[str, str]:
    return build_manage_service_headers(
        correlation_id,
        capability=MANAGE_WRITE_CAPABILITY,
        extras=extras,
    )


def build_manage_pm_quality_read_headers(
    correlation_id: str,
    *,
    extras: dict[str, str] | None = None,
) -> dict[str, str]:
    return build_manage_service_headers(
        correlation_id,
        capability=MANAGE_PM_QUALITY_READ_CAPABILITY,
        extras=extras,
    )


def build_manage_service_headers(
    correlation_id: str,
    *,
    capability: str,
    extras: dict[str, str] | None = None,
) -> dict[str, str]:
    return build_upstream_headers(
        correlation_id,
        extras=extras,
        caller_headers={
            "X-Actor-Id": MANAGE_WRITE_ACTOR_ID,
            "X-Tenant-Id": MANAGE_WRITE_TENANT_ID,
            "X-Role": MANAGE_WRITE_ROLE,
            "X-Service-Identity": MANAGE_WRITE_SERVICE_IDENTITY,
            "X-Capabilities": capability,
        },
    )


def ensure_manage_write_authority(headers: dict[str, str]) -> dict[str, str]:
    authorized = dict(headers)
    authorized.setdefault("X-Actor-Id", MANAGE_WRITE_ACTOR_ID)
    authorized.setdefault("X-Tenant-Id", MANAGE_WRITE_TENANT_ID)
    authorized.setdefault("X-Role", MANAGE_WRITE_ROLE)
    authorized.setdefault("X-Service-Identity", MANAGE_WRITE_SERVICE_IDENTITY)
    capabilities = _capability_set(authorized.get("X-Capabilities"))
    capabilities.add(MANAGE_WRITE_CAPABILITY)
    authorized["X-Capabilities"] = ",".join(sorted(capabilities))
    return authorized


def _capability_set(value: str | None) -> set[str]:
    if value is None:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}
