from app.services.platform_capabilities_service import PlatformCapabilitiesService
from app.services.platform_capabilities_service_factory import (
    build_platform_capabilities_service,
    platform_capabilities_service_signature,
)

_PLATFORM_CAPABILITIES_SERVICE: PlatformCapabilitiesService | None = None
_PLATFORM_CAPABILITIES_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def platform_capabilities_service() -> PlatformCapabilitiesService:
    global _PLATFORM_CAPABILITIES_SERVICE, _PLATFORM_CAPABILITIES_SERVICE_SIGNATURE
    signature = platform_capabilities_service_signature()
    if (
        _PLATFORM_CAPABILITIES_SERVICE is None
        or _PLATFORM_CAPABILITIES_SERVICE_SIGNATURE != signature
    ):
        _PLATFORM_CAPABILITIES_SERVICE = build_platform_capabilities_service()
        _PLATFORM_CAPABILITIES_SERVICE_SIGNATURE = signature
    return _PLATFORM_CAPABILITIES_SERVICE
