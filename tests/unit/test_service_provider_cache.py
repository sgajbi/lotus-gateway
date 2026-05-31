from app.services.service_provider_cache import resolve_cached_service


def test_resolve_cached_service_builds_when_cache_empty() -> None:
    created: list[str] = []

    def build_service() -> str:
        created.append("built")
        return "service-a"

    service, signature = resolve_cached_service(
        service=None,
        cached_signature=None,
        current_signature=("route-a",),
        build_service=build_service,
    )

    assert service == "service-a"
    assert signature == ("route-a",)
    assert created == ["built"]


def test_resolve_cached_service_reuses_matching_signature() -> None:
    created: list[str] = []

    def build_service() -> str:
        created.append("built")
        return "service-b"

    service, signature = resolve_cached_service(
        service="cached-service",
        cached_signature=("route-a",),
        current_signature=("route-a",),
        build_service=build_service,
    )

    assert service == "cached-service"
    assert signature == ("route-a",)
    assert created == []


def test_resolve_cached_service_reuses_falsey_cached_service() -> None:
    created: list[str] = []

    def build_service() -> str:
        created.append("built")
        return "rebuilt-service"

    service, signature = resolve_cached_service(
        service="",
        cached_signature=("route-a",),
        current_signature=("route-a",),
        build_service=build_service,
    )

    assert service == ""
    assert signature == ("route-a",)
    assert created == []


def test_resolve_cached_service_rebuilds_when_signature_changes() -> None:
    created: list[str] = []

    def build_service() -> str:
        created.append("built")
        return "service-b"

    service, signature = resolve_cached_service(
        service="cached-service",
        cached_signature=("route-a",),
        current_signature=("route-b",),
        build_service=build_service,
    )

    assert service == "service-b"
    assert signature == ("route-b",)
    assert created == ["built"]
