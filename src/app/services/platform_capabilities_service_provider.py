from app.services.platform_capabilities_service import PlatformCapabilitiesService
from app.services.platform_capabilities_service_factory import (
    build_platform_capabilities_service,
)


def platform_capabilities_service() -> PlatformCapabilitiesService:
    return build_platform_capabilities_service()
