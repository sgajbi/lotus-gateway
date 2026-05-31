from app.services.composite_performance_service_factory import (
    build_composite_performance_service,
)


def test_composite_performance_service_factory_uses_performance_analytics_client(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_base_url",
        "http://performance:8000",
    )
    monkeypatch.setattr(
        "app.services.analytics_client_factory.settings.performance_analytics_timeout_seconds",
        7.5,
    )

    service = build_composite_performance_service()

    assert service._analytics_client._base_url == "http://performance:8000"
    assert service._analytics_client._timeout == 7.5
