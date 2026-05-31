from app.services.platform_capabilities_service_provider import platform_capabilities_service


def test_platform_capabilities_service_provider_uses_configured_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.platform_capabilities_service_factory.settings.platform_capabilities_source_timeout_seconds",
        9.25,
    )

    assert platform_capabilities_service()._source_timeout_seconds == 9.25
