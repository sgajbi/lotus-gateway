from app.services.platform_capabilities_service import PlatformCapabilitiesService
from app.services.platform_capabilities_service_factory import (
    build_platform_capabilities_service,
    platform_capabilities_service_signature,
)
from app.services.service_provider_cache import resolve_cached_service

_PLATFORM_CAPABILITIES_SERVICE: PlatformCapabilitiesService | None = None
_PLATFORM_CAPABILITIES_SERVICE_SIGNATURE: tuple[object, ...] | None = None


def platform_capabilities_service() -> PlatformCapabilitiesService:
    global _PLATFORM_CAPABILITIES_SERVICE, _PLATFORM_CAPABILITIES_SERVICE_SIGNATURE
    service, signature = resolve_cached_service(
        _PLATFORM_CAPABILITIES_SERVICE,
        _PLATFORM_CAPABILITIES_SERVICE_SIGNATURE,
        platform_capabilities_service_signature(),
        build_platform_capabilities_service,
    )
    _PLATFORM_CAPABILITIES_SERVICE = service
    _PLATFORM_CAPABILITIES_SERVICE_SIGNATURE = signature
    return service
