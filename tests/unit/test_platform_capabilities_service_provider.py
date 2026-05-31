from app.services.platform_capabilities_service_provider import platform_capabilities_service


def test_platform_capabilities_service_provider_uses_configured_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        9.25,
    )

    assert platform_capabilities_service()._source_timeout_seconds == 9.25


def test_platform_capabilities_service_provider_reuses_unchanged_signature(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        7.5,
    )

    first = platform_capabilities_service()
    second = platform_capabilities_service()

    assert first is second


def test_platform_capabilities_service_provider_rebuilds_when_source_timeout_changes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        8.0,
    )
    first = platform_capabilities_service()

    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        8.5,
    )
    second = platform_capabilities_service()

    assert first is not second
    assert second._source_timeout_seconds == 8.5
